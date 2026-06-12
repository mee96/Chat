import { Component } from '@angular/core';
import { ChatComponent } from './chat/chat';
import { Login } from './login/login';

@Component({
  selector: 'app-root',
  imports: [ChatComponent, Login],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  username = '';

  onUserLogged(name: string) {
    this.username = name;
  }
}