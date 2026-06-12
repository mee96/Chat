import { Component, OnInit, OnDestroy, input, signal, WritableSignal } from '@angular/core';
import { FormsModule } from '@angular/forms';

interface Message {
  text: string;
  sender: string;
  time: string;
  isMe: boolean;
}

interface Contact {
  name: string;
  initials: string;
  online: boolean;
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

  readonly availableUsers = signal<User[]>([]);

  readonly activeContact = signal<Contact | null>(null);
  private socket!: WebSocket;

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

  selectContact(contact: Contact) {
    this.activeContact.set(contact);
  }

  startChat(user: User) {
    const existing = this.contacts().find(c => c.name === user.name);
    if (existing) {
      this.activeContact.set(existing);
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
    this.activeContact.set(newContact);
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

    const active = this.activeContact();
    if (!active) return;

    if (this.socket?.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket is not open; message not sent');
      return;
    }

    this.socket.send(`${active.name}:${text}`);

    active.messages.update(msgs => [...msgs, {
      text,
      sender: this.myName(),
      time: this.getTime(),
      isMe: true
    }]);
    active.lastMessage.set(text);
    this.newMessage = '';
  }
}
