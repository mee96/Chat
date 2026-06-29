import { Component, OnInit, OnDestroy, input, signal, computed, WritableSignal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AI_ROOM, AiUsage, parseAiPayload } from './ai-protocol';

interface Message {
  text: string;
  sender: string;
  time: string;
  isMe: boolean;
  usage?: AiUsage;
}

interface Contact {
  name: string;
  initials: string;
  online: boolean;
  lastMessage: WritableSignal<string>;
  messages: WritableSignal<Message[]>;
}

interface Room {
  name: string;
  members: WritableSignal<string[]>;
  lastMessage: WritableSignal<string>;
  messages: WritableSignal<Message[]>;
}

interface User {
  name: string;
  initials: string;
  online: boolean;
}

@Component({
  selector: 'app-chat',
  imports: [FormsModule],
  templateUrl: './chat.html',
  styleUrl: './chat.scss'
})
export class ChatComponent implements OnInit, OnDestroy {

  readonly myName = input('');
  newMessage = '';

  readonly contacts = signal<Contact[]>([]);
  readonly rooms = signal<Room[]>([]);
  readonly availableUsers = signal<User[]>([]);

  readonly activeContact = signal<Contact | null>(null);
  readonly activeRoom = signal<Room | null>(null);

  readonly aiChat = {
    name: AI_ROOM,
    messages: signal<Message[]>([]),
    lastMessage: signal('')
  };
  readonly activeAi = signal(false);
  readonly aiTyping = signal(false);

  // Group creation UI state
  readonly creatingGroup = signal(false);
  readonly selectedForGroup = signal<string[]>([]);
  groupName = '';
  private readonly pendingRoom = signal<string | null>(null);

  private socket!: WebSocket;

  // Unified view of whatever conversation is active (direct or room).
  readonly active = computed(() => {
    if (this.activeAi()) {
      return {
        title: this.aiChat.name,
        subtitle: this.aiTyping() ? 'escrivint…' : 'sempre disponible ✦',
        initials: '🤖',
        online: true,
        isRoom: false,
        isAi: true,
        messages: this.aiChat.messages,
      };
    }
    const c = this.activeContact();
    if (c) {
      return {
        title: c.name,
        subtitle: c.online ? 'en línia ✦' : 'desconnectat/da',
        initials: c.initials,
        online: c.online,
        isRoom: false,
        isAi: false,
        messages: c.messages,
      };
    }
    const r = this.activeRoom();
    if (r) {
      return {
        title: r.name,
        subtitle: r.members().join(', '),
        initials: '#',
        online: false,
        isRoom: true,
        isAi: false,
        messages: r.messages,
      };
    }
    return null;
  });

  ngOnInit() {
    this.connectWebSocket();
  }

  ngOnDestroy() {
    this.socket?.close();
  }

  connectWebSocket() {
    this.socket = new WebSocket(`wss://chat-backend-6g1r.onrender.com/ws/${this.myName()}`);

    this.socket.onmessage = (event) => {
      const data: string = event.data;

      if (data.startsWith('AI:')) {
        this.handleAiMessage(data.slice('AI:'.length));
        return;
      }

      if (data.startsWith('SYSTEM:users:')) {
        const names = data.slice('SYSTEM:users:'.length)
          .split(',')
          .map(n => n.trim())
          .filter(n => n && n !== this.myName());

        this.availableUsers.set(names.map(name => ({
          name,
          initials: name.slice(0, 2).toUpperCase(),
          online: true
        })));
        return;
      }

      if (data.startsWith('SYSTEM:error:')) {
        console.warn('Server:', data.slice('SYSTEM:error:'.length));
        this.pendingRoom.set(null);
        return;
      }

      if (data.startsWith('JOIN:')) {
        this.handleJoin(data);
        return;
      }

      if (data.startsWith('ROOM:')) {
        this.handleRoomMessage(data);
        return;
      }

      // Direct message: sender:message
      const [sender, ...rest] = data.split(':');
      const text = rest.join(':');

      if (sender === this.myName()) return;

      let contact = this.contacts().find(c => c.name === sender);
      if (!contact) {
        contact = {
          name: sender,
          initials: sender.slice(0, 2).toUpperCase(),
          online: true,
          lastMessage: signal(''),
          messages: signal<Message[]>([])
        };
        this.contacts.update(list => [...list, contact!]);
      }

      contact.messages.update(msgs => [...msgs, {
        text,
        sender,
        time: this.getTime(),
        isMe: false
      }]);
      contact.lastMessage.set(text);
    };
  }

  // JOIN:roomname:member1,member2,...  — server confirms room membership
  private handleJoin(data: string) {
    const parts = data.split(':');
    const roomName = parts[1];
    const members = parts.slice(2).join(':')
      .split(',')
      .map(m => m.trim())
      .filter(Boolean);

    let room = this.rooms().find(r => r.name === roomName);
    if (!room) {
      room = {
        name: roomName,
        members: signal(members),
        lastMessage: signal(''),
        messages: signal<Message[]>([])
      };
      this.rooms.update(list => [...list, room!]);
    } else {
      room.members.set(members);
    }

    // If we're the creator waiting on this room, open it.
    if (this.pendingRoom() === roomName) {
      this.activeContact.set(null);
      this.activeRoom.set(room);
      this.pendingRoom.set(null);
    }
  }

  // ROOM:roomname:sender:message  — incoming group message
  private handleRoomMessage(data: string) {
    const parts = data.split(':');
    const roomName = parts[1];
    const sender = parts[2];
    const text = parts.slice(3).join(':');

    if (sender === this.myName()) return;

    const room = this.rooms().find(r => r.name === roomName);
    if (!room) return;

    room.messages.update(msgs => [...msgs, {
      text,
      sender,
      time: this.getTime(),
      isMe: false
    }]);
    room.lastMessage.set(text);
  }

  private handleAiMessage(json: string) {
    this.aiTyping.set(false);

    let payload;
    try {
      payload = parseAiPayload(json);
    } catch {
      console.warn('Invalid AI payload', json);
      return;
    }

    this.aiChat.messages.update(msgs => [...msgs, {
      text: payload.text,
      sender: AI_ROOM,
      time: this.getTime(),
      isMe: false,
      usage: payload.usage ?? undefined
    }]);
    this.aiChat.lastMessage.set(payload.text);
  }

  selectAi() {
    this.activeContact.set(null);
    this.activeRoom.set(null);
    this.activeAi.set(true);
  }

  selectContact(contact: Contact) {
    this.activeAi.set(false);
    this.activeRoom.set(null);
    this.activeContact.set(contact);
  }

  selectRoom(room: Room) {
    this.activeAi.set(false);
    this.activeContact.set(null);
    this.activeRoom.set(room);
  }

  onUserClick(user: User) {
    if (this.creatingGroup()) {
      this.toggleUserSelection(user.name);
    } else {
      this.startChat(user);
    }
  }

  startChat(user: User) {
    const existing = this.contacts().find(c => c.name === user.name);
    if (existing) {
      this.selectContact(existing);
      return;
    }
    const newContact: Contact = {
      name: user.name,
      initials: user.initials,
      online: user.online,
      lastMessage: signal(''),
      messages: signal<Message[]>([])
    };
    this.contacts.update(list => [...list, newContact]);
    this.selectContact(newContact);
  }

  toggleGroupMode() {
    const next = !this.creatingGroup();
    this.creatingGroup.set(next);
    if (!next) {
      this.selectedForGroup.set([]);
      this.groupName = '';
    }
  }

  isSelected(name: string): boolean {
    return this.selectedForGroup().includes(name);
  }

  toggleUserSelection(name: string) {
    this.selectedForGroup.update(list =>
      list.includes(name) ? list.filter(n => n !== name) : [...list, name]
    );
  }

  canCreateGroup(): boolean {
    return this.groupName.trim().length > 0 && this.selectedForGroup().length > 0;
  }

  createGroup() {
    const name = this.groupName.trim();
    const members = this.selectedForGroup();
    if (!name || members.length === 0) return;

    if (this.socket?.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket is not open; group not created');
      return;
    }

    this.socket.send(`JOIN:${name}:${members.join(',')}`);
    this.pendingRoom.set(name);

    this.groupName = '';
    this.selectedForGroup.set([]);
    this.creatingGroup.set(false);
  }

  getTime(): string {
    const now = new Date();
    const h = now.getHours().toString();
    const m = now.getMinutes().toString().padStart(2, '0');
    return `${h}:${m}`;
  }

  sendMessage() {
    const text = this.newMessage.trim();
    if (!text) return;

    if (this.socket?.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket is not open; message not sent');
      return;
    }

    if (this.activeAi()) {
      this.socket.send('AI:' + text);
      this.aiChat.messages.update(msgs => [...msgs, {
        text,
        sender: this.myName(),
        time: this.getTime(),
        isMe: true
      }]);
      this.aiChat.lastMessage.set(text);
      this.aiTyping.set(true);
      this.newMessage = '';
      return;
    }

    const room = this.activeRoom();
    const contact = this.activeContact();

    if (room) {
      this.socket.send(`ROOM:${room.name}:${text}`);
      room.messages.update(msgs => [...msgs, {
        text,
        sender: this.myName(),
        time: this.getTime(),
        isMe: true
      }]);
      room.lastMessage.set(text);
    } else if (contact) {
      this.socket.send(`${contact.name}:${text}`);
      contact.messages.update(msgs => [...msgs, {
        text,
        sender: this.myName(),
        time: this.getTime(),
        isMe: true
      }]);
      contact.lastMessage.set(text);
    } else {
      return;
    }

    this.newMessage = '';
  }
}
