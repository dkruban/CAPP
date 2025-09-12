from flask import Flask, render_template_string, send_file, request
from flask_socketio import SocketIO, send, emit
import datetime
import time
import random
import json
import os
import base64
from io import BytesIO
import threading
import webbrowser
from pyngrok import ngrok

# Try to load environment variables from .env file (for development)
# Make it optional to avoid errors in production
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv is not installed, continue without it
    pass

app = Flask(__name__)
# Use environment variable for SECRET_KEY with fallback
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'secret!')
# Update the SocketIO initialization to use eventlet for production
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")
# File to store chat history
CHAT_HISTORY_FILE = "chat_history.json"
# Store chat history in memory
chat_history = []
online_users = []
# Added: Dictionary to track session IDs and usernames
session_to_user = {}

# Load chat history from file if it exists
def load_chat_history():
    global chat_history
    if os.path.exists(CHAT_HISTORY_FILE):
        try:
            with open(CHAT_HISTORY_FILE, 'r') as f:
                chat_history = json.load(f)
        except:
            chat_history = []

# Save chat history to file
def save_chat_history():
    with open(CHAT_HISTORY_FILE, 'w') as f:
        json.dump(chat_history, f)

# Load chat history at startup
load_chat_history()

# Start ngrok tunnel when app runs
def start_ngrok():
    try:
        # Start ngrok tunnel
        public_url = ngrok.connect(5000).public_url
        print(f" * ngrok tunnel available at: {public_url}")
        
        # Store public URL in app config
        app.config['PUBLIC_URL'] = public_url
        
        # Open browser automatically
        threading.Timer(1.25, lambda: webbrowser.open(public_url)).start()
        
        return public_url
    except Exception as e:
        print(f"Error starting ngrok: {e}")
        print("Make sure you have ngrok installed: pip install pyngrok")
        return None

html = """
<!DOCTYPE html>
<html>
<head>
    <title>DK port</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
        
        :root {
            --primary: #00a8ff;
            --primary-dark: #0097e6;
            --secondary: #2ecc71;
            --background: #0a192f;
            --surface: #172a45;
            --surface-light: #233554;
            --text: #e6f1ff;
            --text-secondary: #8892b0;
            --accent: #64ffda;
            --success: #2ecc71;
            --gradient: linear-gradient(135deg, #00a8ff, #2ecc71);
            --message-gradient: linear-gradient(135deg, #0097e6, #00a8ff);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Poppins', sans-serif;
            background: var(--background);
            color: var(--text);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
            position: relative;
        }
        
        /* Electric Animation Background */
        .electric-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            overflow: hidden;
        }
        
        .electric-bolt {
            position: absolute;
            width: 2px;
            height: 80px;
            background: linear-gradient(to bottom, 
                transparent 0%, 
                rgba(0, 168, 255, 0.8) 20%, 
                rgba(100, 255, 218, 1) 50%, 
                rgba(0, 168, 255, 0.8) 80%, 
                transparent 100%);
            filter: blur(1px);
            opacity: 0;
            transform-origin: center;
        }
        
        .electric-bolt::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: inherit;
            filter: blur(4px);
            opacity: 0.7;
        }
        
        .electric-bolt::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: inherit;
            filter: blur(8px);
            opacity: 0.5;
        }
        
        /* Create multiple bolts with different animations */
        .bolt1 {
            top: 10%;
            left: -100px;
            animation: electric-pass1 8s linear infinite;
            animation-delay: 0s;
        }
        
        .bolt2 {
            top: 30%;
            left: -100px;
            animation: electric-pass2 12s linear infinite;
            animation-delay: 1s;
        }
        
        .bolt3 {
            top: 50%;
            left: -100px;
            animation: electric-pass3 10s linear infinite;
            animation-delay: 2s;
        }
        
        .bolt4 {
            top: 70%;
            left: -100px;
            animation: electric-pass4 9s linear infinite;
            animation-delay: 3s;
        }
        
        .bolt5 {
            top: 90%;
            left: -100px;
            animation: electric-pass5 11s linear infinite;
            animation-delay: 4s;
        }
        
        @keyframes electric-pass1 {
            0% {
                transform: translateX(0) rotate(25deg);
                opacity: 0;
            }
            10% {
                opacity: 1;
            }
            90% {
                opacity: 1;
            }
            100% {
                transform: translateX(calc(100vw + 200px)) rotate(25deg);
                opacity: 0;
            }
        }
        
        @keyframes electric-pass2 {
            0% {
                transform: translateX(0) rotate(-20deg);
                opacity: 0;
            }
            10% {
                opacity: 1;
            }
            90% {
                opacity: 1;
            }
            100% {
                transform: translateX(calc(100vw + 200px)) rotate(-20deg);
                opacity: 0;
            }
        }
        
        @keyframes electric-pass3 {
            0% {
                transform: translateX(0) rotate(15deg);
                opacity: 0;
            }
            10% {
                opacity: 1;
            }
            90% {
                opacity: 1;
            }
            100% {
                transform: translateX(calc(100vw + 200px)) rotate(15deg);
                opacity: 0;
            }
        }
        
        @keyframes electric-pass4 {
            0% {
                transform: translateX(0) rotate(-30deg);
                opacity: 0;
            }
            10% {
                opacity: 1;
            }
            90% {
                opacity: 1;
            }
            100% {
                transform: translateX(calc(100vw + 200px)) rotate(-30deg);
                opacity: 0;
            }
        }
        
        @keyframes electric-pass5 {
            0% {
                transform: translateX(0) rotate(40deg);
                opacity: 0;
            }
            10% {
                opacity: 1;
            }
            90% {
                opacity: 1;
            }
            100% {
                transform: translateX(calc(100vw + 200px)) rotate(40deg);
                opacity: 0;
            }
        }
        
        .chat-container {
            width: 90%;
            max-width: 450px;
            height: 90vh;
            max-height: 700px;
            background: var(--surface);
            border-radius: 24px;
            box-shadow: 0 25px 80px rgba(0, 168, 255, 0.3), 
                        0 0 0 1px rgba(100, 255, 218, 0.1);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            position: relative;
            z-index: 1;
        }
        
        .header {
            background: var(--gradient);
            color: white;
            padding: 18px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.3) 0%, rgba(255,255,255,0) 70%);
            animation: pulse 4s infinite ease-in-out;
        }
        
        @keyframes pulse {
            0%, 100% { 
                transform: scale(0.8);
                opacity: 0.5;
            }
            50% { 
                transform: scale(1.2);
                opacity: 0.8;
            }
        }
        
        .header h1 {
            font-size: 24px;
            font-weight: 700;
            letter-spacing: 1px;
            position: relative;
            z-index: 1;
            text-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 14px;
            opacity: 0.9;
            margin-top: 6px;
            position: relative;
            z-index: 1;
        }
        
        .online-indicator {
            position: absolute;
            top: 15px;
            right: 15px;
            display: flex;
            align-items: center;
            background: rgba(0, 0, 0, 0.2);
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            z-index: 2;
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            background: var(--success);
            border-radius: 50%;
            margin-right: 6px;
            animation: blink 2s infinite;
        }
        
        @keyframes blink {
            0%, 100% { 
                opacity: 1;
                transform: scale(1);
            }
            50% { 
                opacity: 0.7;
                transform: scale(1.2);
            }
        }
        
        .users-online {
            position: absolute;
            top: 50px;
            right: 15px;
            display: flex;
            align-items: center;
            background: rgba(0, 0, 0, 0.2);
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            z-index: 2;
        }
        
        .user-avatar {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin-left: -6px;
            border: 2px solid var(--primary);
        }
        
        .user-avatar:first-child {
            margin-left: 6px;
        }
        
        #chat {
            flex: 1;
            padding: 15px;
            overflow-y: auto;
            background: var(--surface);
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        
        #chat::-webkit-scrollbar {
            width: 6px;
        }
        
        #chat::-webkit-scrollbar-track {
            background: var(--surface-light);
            border-radius: 3px;
        }
        
        #chat::-webkit-scrollbar-thumb {
            background: var(--primary);
            border-radius: 3px;
        }
        
        .date-separator {
            text-align: center;
            margin: 8px 0;
            position: relative;
            color: var(--text-secondary);
            font-size: 12px;
        }
        
        .date-separator::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 0;
            right: 0;
            height: 1px;
            background: var(--surface-light);
            z-index: 1;
        }
        
        .date-separator span {
            background: var(--surface);
            padding: 0 10px;
            position: relative;
            z-index: 2;
        }
        
        .msg {
            max-width: 75%;
            padding: 12px 15px;
            border-radius: 18px;
            font-size: 14px;
            line-height: 1.4;
            position: relative;
            animation: fadeInUp 0.4s ease;
            word-wrap: break-word;
            transition: transform 0.2s ease;
        }
        
        .msg:hover {
            transform: translateY(-2px);
        }
        
        @keyframes fadeInUp {
            from { 
                opacity: 0;
                transform: translateY(10px);
            }
            to { 
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .me {
            background: var(--message-gradient);
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 4px;
            box-shadow: 0 4px 12px rgba(0, 168, 255, 0.3);
        }
        
        .other {
            background: var(--surface-light);
            color: var(--text);
            margin-right: auto;
            border-bottom-left-radius: 4px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }
        
        .msg-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 5px;
        }
        
        .msg-user {
            font-weight: 600;
            font-size: 12px;
        }
        
        .me .msg-user {
            color: rgba(255, 255, 255, 0.9);
        }
        
        .other .msg-user {
            color: var(--accent);
        }
        
        .time {
            font-size: 11px;
            opacity: 0.7;
        }
        
        .msg-status {
            display: flex;
            align-items: center;
            margin-top: 5px;
            font-size: 11px;
            opacity: 0.8;
        }
        
        .status-icon {
            width: 14px;
            height: 14px;
            margin-left: 4px;
        }
        
        .input-area {
            display: flex;
            padding: 15px;
            background: var(--surface);
            border-top: 1px solid var(--surface-light);
        }
        
        .input-wrapper {
            display: flex;
            background: var(--surface-light);
            border-radius: 25px;
            padding: 6px;
            flex: 1;
            margin-right: 10px;
            box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.2);
        }
        
        .input-area input {
            border: none;
            padding: 10px 14px;
            outline: none;
            background: transparent;
            color: var(--text);
            font-size: 14px;
            flex: 1;
        }
        
        .input-area input::placeholder {
            color: var(--text-secondary);
        }
        
        .input-actions {
            display: flex;
            gap: 8px;
        }
        
        .action-btn {
            background: var(--surface-light);
            color: var(--text);
            border: none;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            cursor: pointer;
            display: flex;
            justify-content: center;
            align-items: center;
            transition: all 0.2s ease;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        }
        
        .action-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 168, 255, 0.3);
        }
        
        .action-btn.recording {
            background: var(--gradient);
            animation: pulse 1.5s infinite;
        }
        
        .send-btn {
            background: var(--gradient);
            color: white;
            border: none;
            border-radius: 50%;
            width: 44px;
            height: 44px;
            cursor: pointer;
            display: flex;
            justify-content: center;
            align-items: center;
            transition: all 0.2s ease;
            box-shadow: 0 2px 8px rgba(0, 168, 255, 0.3);
        }
        
        .send-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 168, 255, 0.4);
        }
        
        .icon {
            width: 20px;
            height: 20px;
        }
        
        .typing-indicator {
            display: none;
            padding: 8px 12px;
            background: var(--surface-light);
            border-radius: 16px;
            width: fit-content;
            margin-bottom: 8px;
            font-size: 12px;
            color: var(--text-secondary);
        }
        
        .typing-dots span {
            display: inline-block;
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--text-secondary);
            margin: 0 2px;
            animation: typing 1.4s infinite;
        }
        
        .typing-dots span:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        .typing-dots span:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes typing {
            0%, 60%, 100% {
                transform: translateY(0);
            }
            30% {
                transform: translateY(-6px);
            }
        }
        
        .chat-history-notification {
            text-align: center;
            padding: 10px;
            margin: 8px 0;
            background: rgba(0, 168, 255, 0.2);
            border-radius: 10px;
            font-size: 12px;
            color: var(--accent);
            animation: pulse 2s infinite;
        }
        
        .theme-toggle {
            position: absolute;
            top: 15px;
            left: 15px;
            width: 40px;
            height: 20px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            cursor: pointer;
            z-index: 10;
        }
        
        .theme-toggle-slider {
            position: absolute;
            top: 2px;
            left: 2px;
            width: 16px;
            height: 16px;
            background: white;
            border-radius: 50%;
            transition: transform 0.3s ease;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        
        .theme-toggle.active .theme-toggle-slider {
            transform: translateX(20px);
        }
        
        .public-url {
            position: absolute;
            top: 15px;
            left: 60px;
            background: rgba(0, 0, 0, 0.5);
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            z-index: 10;
            max-width: 200px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .voice-recording {
            display: none;
            position: fixed;
            bottom: 80px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--surface);
            padding: 15px;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.3);
            z-index: 100;
            text-align: center;
            animation: fadeInUp 0.3s ease;
        }
        
        .voice-wave {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 40px;
            margin: 10px 0;
        }
        
        .voice-bar {
            width: 4px;
            height: 20px;
            background: var(--gradient);
            margin: 0 2px;
            border-radius: 2px;
            animation: wave 1s infinite ease-in-out;
        }
        
        .voice-bar:nth-child(2) {
            animation-delay: 0.1s;
        }
        
        .voice-bar:nth-child(3) {
            animation-delay: 0.2s;
        }
        
        .voice-bar:nth-child(4) {
            animation-delay: 0.3s;
        }
        
        .voice-bar:nth-child(5) {
            animation-delay: 0.4s;
        }
        
        @keyframes wave {
            0%, 100% {
                transform: scaleY(0.5);
            }
            50% {
                transform: scaleY(1.5);
            }
        }
        
        .voice-message {
            display: flex;
            align-items: center;
            margin-top: 8px;
            gap: 10px;
        }
        
        .voice-player {
            flex: 1;
        }
        
        .voice-download {
            background: rgba(255, 255, 255, 0.1);
            border: none;
            border-radius: 50%;
            width: 32px;
            height: 32px;
            cursor: pointer;
            display: flex;
            justify-content: center;
            align-items: center;
            transition: all 0.2s ease;
        }
        
        .voice-download:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: scale(1.1);
        }
        
        .voice-download-icon {
            width: 16px;
            height: 16px;
        }
        
        .image-preview {
            max-width: 150px;
            max-height: 150px;
            border-radius: 8px;
            margin-top: 8px;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.2);
        }
        
        .file-input {
            display: none;
        }
        
        /* Light theme */
        body.light-theme {
            --background: #f5f7fa;
            --surface: #ffffff;
            --surface-light: #e9ecef;
            --text: #2d3748;
            --text-secondary: #718096;
        }
        
        body.light-theme .chat-container {
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1), 
                        0 0 0 1px rgba(0, 0, 0, 0.05);
        }
        
        body.light-theme .header::before {
            background: radial-gradient(circle, rgba(255,255,255,0.5) 0%, rgba(255,255,255,0) 70%);
        }
        
        body.light-theme .online-indicator,
        body.light-theme .users-online {
            background: rgba(0, 0, 0, 0.05);
        }
        
        body.light-theme .date-separator::before {
            background: var(--surface-light);
        }
        
        body.light-theme .date-separator span {
            background: var(--surface);
        }
        
        body.light-theme .msg {
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }
        
        body.light-theme .me {
            box-shadow: 0 2px 8px rgba(0, 168, 255, 0.2);
        }
        
        body.light-theme .other {
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        body.light-theme .input-wrapper {
            box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.05);
        }
        
        body.light-theme .action-btn {
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        body.light-theme .action-btn:hover {
            box-shadow: 0 4px 12px rgba(0, 168, 255, 0.2);
        }
        
        body.light-theme .send-btn {
            box-shadow: 0 2px 8px rgba(0, 168, 255, 0.2);
        }
        
        body.light-theme .send-btn:hover {
            box-shadow: 0 4px 12px rgba(0, 168, 255, 0.3);
        }
        
        body.light-theme .voice-recording {
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
        }
        
        /* Responsive adjustments */
        @media (max-width: 480px) {
            .chat-container {
                width: 100%;
                height: 100vh;
                max-height: 100vh;
                border-radius: 0;
            }
            
            .header h1 {
                font-size: 20px;
            }
            
            .header p {
                font-size: 12px;
            }
            
            .online-indicator,
            .users-online {
                font-size: 10px;
                padding: 3px 8px;
            }
            
            .status-dot {
                width: 6px;
                height: 6px;
            }
            
            .user-avatar {
                width: 16px;
                height: 16px;
            }
            
            #chat {
                padding: 12px;
            }
            
            .msg {
                font-size: 13px;
                padding: 10px 12px;
            }
            
            .input-area {
                padding: 12px;
            }
            
            .action-btn,
            .send-btn {
                width: 36px;
                height: 36px;
            }
            
            .icon {
                width: 18px;
                height: 18px;
            }
            
            .public-url {
                max-width: 120px;
                font-size: 10px;
            }
        }
    </style>
</head>
<body>
    <!-- Electric Background Animation -->
    <div class="electric-bg">
        <div class="electric-bolt bolt1"></div>
        <div class="electric-bolt bolt2"></div>
        <div class="electric-bolt bolt3"></div>
        <div class="electric-bolt bolt4"></div>
        <div class="electric-bolt bolt5"></div>
    </div>
    
    <div class="chat-container">
        <div class="header">
            <div class="theme-toggle" id="themeToggle">
                <div class="theme-toggle-slider"></div>
            </div>
            <div class="public-url" id="publicUrl" style="display: none;">Public URL: <span id="publicUrlValue"></span></div>
            <h1>💬 Silent Port</h1>
            <p>Connect with your campus community</p>
            <div class="online-indicator">
                <div class="status-dot"></div>
                <span>Online</span>
            </div>
            <div class="users-online" id="usersOnline">
                <span>Online:</span>
            </div>
        </div>
        
        <div id="chat">
            <div class="chat-history-notification" id="historyNotification">
                Loading chat history...
            </div>
            <div class="typing-indicator" id="typingIndicator">
                Someone is typing
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        </div>
        
        <div class="input-area">
            <div class="input-wrapper">
                <input type="text" id="user" placeholder="Your Name" required>
                <input type="text" id="text" placeholder="Type a message..." required>
            </div>
            <div class="input-actions">
                <button class="action-btn" id="voiceBtn" title="Voice Message">
                    <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"></path>
                    </svg>
                </button>
                <button class="action-btn" id="imageBtn" title="Share Image">
                    <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                    </svg>
                </button>
                <input type="file" id="fileInput" class="file-input" accept="image/*">
                <button class="send-btn" onclick="sendMessage()">
                    <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7"></path>
                    </svg>
                </button>
            </div>
        </div>
    </div>
    
    <div class="voice-recording" id="voiceRecording">
        <p>Recording voice message...</p>
        <div class="voice-wave">
            <div class="voice-bar"></div>
            <div class="voice-bar"></div>
            <div class="voice-bar"></div>
            <div class="voice-bar"></div>
            <div class="voice-bar"></div>
        </div>
        <button class="send-btn" onclick="sendVoiceMessage()">
            <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
        </button>
    </div>
    
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script>
        var socket = io();
        var chat = document.getElementById("chat");
        var username = "";
        var typingTimer;
        var isTyping = false;
        var lastDate = null;
        var isRecording = false;
        var mediaRecorder;
        var audioChunks = [];
        
        // Theme toggle
        document.getElementById("themeToggle").addEventListener("click", function() {
            document.body.classList.toggle("light-theme");
            this.classList.toggle("active");
        });
        
        // Function to format date
        function formatDate(dateString) {
            const date = new Date(dateString);
            const today = new Date();
            const yesterday = new Date(today);
            yesterday.setDate(yesterday.getDate() - 1);
            
            if (date.toDateString() === today.toDateString()) {
                return "Today";
            } else if (date.toDateString() === yesterday.toDateString()) {
                return "Yesterday";
            } else {
                return date.toLocaleDateString('en-US', { 
                    weekday: 'short', 
                    month: 'short', 
                    day: 'numeric' 
                });
            }
        }
        
        // Function to format time
        function formatTime(dateString) {
            const date = new Date(dateString);
            return date.toLocaleTimeString('en-US', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
        }
        
        // Function to add date separator
        function addDateSeparator(dateString) {
            const formattedDate = formatDate(dateString);
            if (lastDate !== formattedDate) {
                const separator = document.createElement("div");
                separator.className = "date-separator";
                separator.innerHTML = `<span>${formattedDate}</span>`;
                chat.appendChild(separator);
                lastDate = formattedDate;
            }
        }
        
        // Function to render message
        function renderMessage(msg) {
            addDateSeparator(msg.datetime);
            
            const cls = (msg.user === username) ? "me" : "other";
            const bubble = document.createElement("div");
            bubble.className = `msg ${cls}`;
            
            let messageContent = msg.text;
            if (msg.type === "image") {
                messageContent = `<img src="${msg.text}" alt="Shared Image" class="image-preview">`;
            } else if (msg.type === "voice") {
                const audioId = "audio_" + msg.id.replace(/[^a-zA-Z0-9]/g, '');
                messageContent = `
                    <div class="voice-message">
                        <div class="voice-player">
                            <audio id="${audioId}" controls>
                                <source src="${msg.text}" type="audio/wav">
                                Your browser does not support the audio element.
                            </audio>
                        </div>
                        <button class="voice-download" onclick="downloadVoice('${msg.text}', '${msg.user}_${msg.datetime}')">
                            <svg class="voice-download-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>
                            </svg>
                        </button>
                    </div>
                `;
            }
            
            bubble.innerHTML = `
                <div class="msg-header">
                    <span class="msg-user">${msg.user}</span>
                    <span class="time">${formatTime(msg.datetime)}</span>
                </div>
                ${messageContent}
                <div class="msg-status">
                    Sent
                    ${msg.status === "delivered" ? '<svg class="status-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>' : ''}
                    ${msg.status === "read" ? '<svg class="status-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>' : ''}
                </div>
            `;
            chat.appendChild(bubble);
            chat.scrollTop = chat.scrollHeight;
        }
        
        // Function to load chat history
        function loadChatHistory(history) {
            // Clear existing messages except typing indicator
            const typingIndicator = document.getElementById("typingIndicator");
            chat.innerHTML = '';
            chat.appendChild(typingIndicator);
            
            // Add history notification
            const historyNotification = document.createElement("div");
            historyNotification.className = "chat-history-notification";
            historyNotification.textContent = `Chat history loaded (${history.length} messages)`;
            chat.appendChild(historyNotification);
            
            // Render each message
            history.forEach(msg => {
                renderMessage(msg);
            });
            
            // Hide notification after 3 seconds
            setTimeout(() => {
                historyNotification.style.display = "none";
            }, 3000);
        }
        
        // Function to update online users
        function updateOnlineUsers(users) {
            const usersContainer = document.getElementById("usersOnline");
            usersContainer.innerHTML = '<span>Online:</span>';
            
            users.forEach(user => {
                const avatar = document.createElement("div");
                avatar.className = "user-avatar";
                avatar.style.background = `hsl(${Math.random() * 360}, 70%, 60%)`;
                avatar.title = user;
                usersContainer.appendChild(avatar);
            });
        }
        
        // Function to download voice message
        function downloadVoice(dataUrl, filename) {
            const link = document.createElement('a');
            link.href = dataUrl;
            link.download = `${filename}.wav`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
        
        // Function to show public URL
        function showPublicUrl(url) {
            if (url) {
                document.getElementById("publicUrlValue").textContent = url;
                document.getElementById("publicUrl").style.display = "block";
            }
        }
        
        socket.on("connect", function() {
            // Request chat history when connected
            socket.emit("request_history");
            
            // Request online users
            socket.emit("request_users");
            
            // Request public URL
            socket.emit("request_public_url");
            
            // Notify server that user is online
            if (username) {
                socket.emit("user_online", { user: username });
            }
        });
        
        socket.on("message", function(msg){
            renderMessage(msg);
            
            // Update message status to "read" after a delay
            if (msg.user === username) {
                setTimeout(() => {
                    msg.status = "read";
                    socket.emit("update_message_status", { id: msg.id, status: "read" });
                }, 2000);
            }
        });
        
        socket.on("chat_history", function(history) {
            loadChatHistory(history);
        });
        
        socket.on("online_users", function(users) {
            online_users = users;
            updateOnlineUsers(users);
        });
        
        socket.on("public_url", function(url) {
            showPublicUrl(url);
        });
        
        socket.on("user_joined", function(data) {
            online_users.push(data.user);
            updateOnlineUsers(online_users);
            
            // Show notification
            showNotification(`${data.user} joined the chat`);
        });
        
        socket.on("user_left", function(data) {
            online_users = online_users.filter(user => user !== data.user);
            updateOnlineUsers(online_users);
            
            // Show notification
            showNotification(`${data.user} left the chat`);
        });
        
        socket.on("typing", function(data) {
            if (data.user !== username) {
                document.getElementById("typingIndicator").style.display = "block";
                clearTimeout(typingTimer);
                typingTimer = setTimeout(function() {
                    document.getElementById("typingIndicator").style.display = "none";
                }, 1000);
            }
        });
        
        socket.on("message_status_updated", function(data) {
            // Update message status in the UI
            const messages = document.querySelectorAll('.msg');
            messages.forEach(msg => {
                const userElement = msg.querySelector('.msg-user');
                if (userElement && userElement.textContent === data.user) {
                    const statusElement = msg.querySelector('.msg-status');
                    if (statusElement) {
                        if (data.status === "delivered") {
                            statusElement.innerHTML = 'Delivered <svg class="status-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>';
                        } else if (data.status === "read") {
                            statusElement.innerHTML = 'Read <svg class="status-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>';
                        }
                    }
                }
            });
        });
        
        function sendMessage() {
            if (!username) {
                username = document.getElementById("user").value;
                if (!username) {
                    showNotification("Please enter your name first!");
                    return;
                }
                // Notify server that user is online
                socket.emit("user_online", { user: username });
            }
            
            var text = document.getElementById("text").value;
            if(username && text){
                const now = new Date();
                const messageId = "msg_" + Date.now() + "_" + Math.random().toString(36).substr(2, 9);
                socket.send({
                    id: messageId,
                    user: username, 
                    text: text,
                    datetime: now.toISOString(),
                    type: "text",
                    status: "sent"
                });
                document.getElementById("text").value = "";
                isTyping = false;
            }
        }
        
        // Voice recording functionality
        document.getElementById("voiceBtn").addEventListener("click", function() {
            if (!username) {
                username = document.getElementById("user").value;
                if (!username) {
                    showNotification("Please enter your name first!");
                    return;
                }
                // Notify server that user is online
                socket.emit("user_online", { user: username });
            }
            
            if (!isRecording) {
                startRecording();
            } else {
                stopRecording();
            }
        });
        
        function startRecording() {
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(stream => {
                    mediaRecorder = new MediaRecorder(stream);
                    audioChunks = [];
                    
                    mediaRecorder.ondataavailable = event => {
                        audioChunks.push(event.data);
                    };
                    
                    mediaRecorder.onstop = () => {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                        const reader = new FileReader();
                        
                        reader.onloadend = function() {
                            const base64data = reader.result;
                            
                            const now = new Date();
                            const messageId = "msg_" + Date.now() + "_" + Math.random().toString(36).substr(2, 9);
                            socket.send({
                                id: messageId,
                                user: username, 
                                text: base64data,
                                datetime: now.toISOString(),
                                type: "voice",
                                status: "sent"
                            });
                        };
                        
                        reader.readAsDataURL(audioBlob);
                    };
                    
                    mediaRecorder.start();
                    isRecording = true;
                    
                    // Update UI
                    document.getElementById("voiceBtn").classList.add("recording");
                    document.getElementById("voiceRecording").style.display = "block";
                })
                .catch(err => {
                    console.error('Error accessing microphone:', err);
                    showNotification("Could not access microphone");
                });
        }
        
        function stopRecording() {
            if (mediaRecorder && mediaRecorder.state !== "inactive") {
                mediaRecorder.stop();
                mediaRecorder.stream.getTracks().forEach(track => track.stop());
            }
            
            isRecording = false;
            
            // Update UI
            document.getElementById("voiceBtn").classList.remove("recording");
            document.getElementById("voiceRecording").style.display = "none";
        }
        
        function sendVoiceMessage() {
            stopRecording();
        }
        
        function showNotification(message) {
            var notification = document.createElement("div");
            notification.style.position = "fixed";
            notification.style.top = "20px";
            notification.style.left = "50%";
            notification.style.transform = "translateX(-50%)";
            notification.style.background = "var(--primary)";
            notification.style.color = "white";
            notification.style.padding = "10px 20px";
            notification.style.borderRadius = "20px";
            notification.style.boxShadow = "0 4px 15px rgba(0,0,0,0.2)";
            notification.style.zIndex = "1000";
            notification.style.animation = "fadeInUp 0.3s ease";
            notification.textContent = message;
            document.body.appendChild(notification);
            
            setTimeout(function() {
                notification.style.animation = "fadeInUp 0.3s ease reverse";
                setTimeout(function() {
                    document.body.removeChild(notification);
                }, 300);
            }, 2000);
        }
        
        // Allow pressing Enter to send message
        document.getElementById("text").addEventListener("keypress", function(event) {
            if (event.key === "Enter") {
                event.preventDefault();
                sendMessage();
            }
        });
        
        // Typing indicator
        document.getElementById("text").addEventListener("input", function() {
            if (username && !isTyping) {
                isTyping = true;
                socket.emit("typing", { user: username });
            }
        });
        
        // Image sharing button
        document.getElementById("imageBtn").addEventListener("click", function() {
            if (!username) {
                username = document.getElementById("user").value;
                if (!username) {
                    showNotification("Please enter your name first!");
                    return;
                }
                // Notify server that user is online
                socket.emit("user_online", { user: username });
            }
            
            document.getElementById("fileInput").click();
        });
        
        // File input change
        document.getElementById("fileInput").addEventListener("change", function(event) {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const now = new Date();
                    const messageId = "msg_" + Date.now() + "_" + Math.random().toString(36).substr(2, 9);
                    socket.send({
                        id: messageId,
                        user: username, 
                        text: e.target.result,
                        datetime: now.toISOString(),
                        type: "image",
                        status: "sent"
                    });
                };
                reader.readAsDataURL(file);
            }
        });
    </script>
</body>
</html>
"""
@app.route("/")
def index():
    return render_template_string(html, public_url=app.config.get('PUBLIC_URL', ''))
@app.route("/download/<filename>")
def download_file(filename):
    # This is a placeholder for file download functionality
    # In a real implementation, you would serve the actual file
    return "File download functionality would be implemented here"
@socketio.on("message")
def handleMessage(msg):
    # Add timestamp if not provided
    if 'datetime' not in msg:
        msg['datetime'] = datetime.datetime.now().isoformat()
    
    # Add to chat history
    chat_history.append(msg)
    
    # Save chat history to file
    save_chat_history()
    
    # Broadcast to all clients
    send(msg, broadcast=True)
    
    # Update message status to "delivered" after a delay
    if msg.get('status') == 'sent':
        # Fixed: Use socketio.sleep instead of time.sleep to avoid blocking
        socketio.sleep(1)  # Simulate network delay
        msg['status'] = 'delivered'
        emit("message_status_updated", msg, broadcast=True)
@socketio.on("update_message_status")
def update_message_status(data):
    # Find the message in history and update status
    for msg in chat_history:
        if msg.get('id') == data.get('id'):
            msg['status'] = data.get('status')
            break
    
    # Save updated chat history
    save_chat_history()
    
    # Broadcast status update
    emit("message_status_updated", data, broadcast=True)
@socketio.on("request_history")
def handle_history_request():
    # Send chat history to the requesting client
    emit("chat_history", chat_history)
@socketio.on("request_users")
def handle_users_request():
    # Send online users to the requesting client
    emit("online_users", online_users)
@socketio.on("request_public_url")
def handle_public_url_request():
    # Send public URL to the requesting client
    emit("public_url", app.config.get('PUBLIC_URL', ''))
@socketio.on("user_online")
def handle_user_online(data):
    user = data.get('user')
    if user and user not in online_users:
        online_users.append(user)
        # Fixed: Track session ID to username mapping
        session_to_user[request.sid] = user
        emit("user_joined", data, broadcast=True)
        emit("online_users", online_users, broadcast=True)
@socketio.on("typing")
def handleTyping(data):
    socketio.emit("typing", data, broadcast=True)
@socketio.on("disconnect")
def handle_disconnect():
    # Fixed: Properly handle user disconnect using session mapping
    username = session_to_user.get(request.sid)
    if username:
        if username in online_users:
            online_users.remove(username)
        # Remove from session mapping
        del session_to_user[request.sid]
        emit("user_left", {"user": username}, broadcast=True)
        emit("online_users", online_users, broadcast=True)

# Update the main block
if __name__ == "__main__":
    # Only start ngrok in development
    if os.environ.get('ENVIRONMENT') != 'production':
        public_url = start_ngrok()
        if public_url:
            print(f" * Public URL: {public_url}")
    
    port = int(os.environ.get('PORT', 5000))
    print(" * Starting Flask-SocketIO server...")
    print(f" * Local URL: http://localhost:{port}")
    socketio.run(app, host="0.0.0.0", port=port)
