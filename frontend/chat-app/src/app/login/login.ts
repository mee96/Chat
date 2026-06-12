import { Component, Output, EventEmitter } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-login',
  imports: [FormsModule],
  templateUrl: './login.html',
  styleUrl: './login.scss',
})
export class Login {
  username = '';

  @Output() userLogged = new EventEmitter<string>();

  enter() {
    if (!this.username.trim()) return;
    this.userLogged.emit(this.username.trim());
  }
}