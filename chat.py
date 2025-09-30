# Apply eventlet monkey patch at the very beginning
import eventlet
eventlet.monkey_patch()

# Now import the rest of the modules
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
# Added: Dictionary to track active calls
active_calls = {}
# Added: Dictionary to map users to their call partners
user_call_partner = {}

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
            --call-gradient: linear-gradient(135deg, #2ecc71, #27ae60);
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
        
        .action-btn.calling {
            background: var(--call-gradient);
            animation: pulse 1.5s infinite;
        }
        
        /* Ensure call button is visible */
        #callBtn {
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            z-index: 10 !important;
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
        
        /* Call UI */
        .call-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }
        
        .call-container {
            width: 90%;
            max-width: 400px;
            background: var(--surface);
            border-radius: 24px;
            padding: 30px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            animation: fadeInUp 0.3s ease;
        }
        
        .call-avatar {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            margin: 0 auto 20px;
            background: var(--gradient);
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 48px;
            color: white;
        }
        
        .call-status {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 10px;
        }
        
        .call-timer {
            font-size: 18px;
            color: var(--text-secondary);
            margin-bottom: 30px;
        }
        
        .call-actions {
            display: flex;
            justify-content: center;
            gap: 20px;
        }
        
        .call-btn {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            border: none;
            cursor: pointer;
            display: flex;
            justify-content: center;
            align-items: center;
            transition: all 0.2s ease;
        }
        
        .call-btn.answer {
            background: var(--success);
            color: white;
        }
        
        .call-btn.reject {
            background: #e74c3c;
            color: white;
        }
        
        .call-btn.end {
            background: #e74c3c;
            color: white;
        }
        
        .call-btn.mute {
            background: var(--surface-light);
            color: var(--text);
        }
        
        .call-btn.muted {
            background: #e74c3c;
            color: white;
        }
        
        .call-btn:hover {
            transform: scale(1.1);
        }
        
        .call-icon {
            width: 24px;
            height: 24px;
        }
        
        .incoming-call-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }
        
        .incoming-call-container {
            width: 90%;
            max-width: 400px;
            background: var(--surface);
            border-radius: 24px;
            padding: 30px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            animation: fadeInUp 0.3s ease;
        }
        
        .incoming-call-avatar {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            margin: 0 auto 20px;
            background: var(--gradient);
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 48px;
            color: white;
        }
        
        .incoming-call-status {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 10px;
        }
        
        .incoming-call-user {
            font-size: 18px;
            color: var(--text-secondary);
            margin-bottom: 30px;
        }
        
        .incoming-call-actions {
            display: flex;
            justify-content: center;
            gap: 20px;
        }
        
        .user-select-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }
        
        .user-select-container {
            width: 90%;
            max-width: 400px;
            background: var(--surface);
            border-radius: 24px;
            padding: 30px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            animation: fadeInUp 0.3s ease;
        }
        
        .user-select-title {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 20px;
        }
        
        .user-list {
            max-height: 300px;
            overflow-y: auto;
            margin-bottom: 20px;
        }
        
        .user-item {
            display: flex;
            align-items: center;
            padding: 12px;
            border-radius: 12px;
            margin-bottom: 10px;
            background: var(--surface-light);
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .user-item:hover {
            background: var(--primary);
            transform: translateY(-2px);
        }
        
        .user-item-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            margin-right: 12px;
            background: var(--gradient);
            display: flex;
            justify-content: center;
            align-items: center;
            color: white;
            font-weight: 600;
        }
        
        .user-item-name {
            flex: 1;
            text-align: left;
        }
        
        .user-item-status {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--success);
        }
        
        .cancel-btn {
            background: var(--surface-light);
            color: var(--text);
            border: none;
            border-radius: 20px;
            padding: 10px 20px;
            cursor: pointer;
            font-size: 16px;
            transition: all 0.2s ease;
        }
        
        .cancel-btn:hover {
            background: #e74c3c;
            color: white;
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
        
        body.light-theme .call-container,
        body.light-theme .incoming-call-container,
        body.light-theme .user-select-container {
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
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
            
            .call-container,
            .incoming-call-container,
            .user-select-container {
                width: 95%;
                padding: 20px;
            }
            
            .call-avatar,
            .incoming-call-avatar {
                width: 100px;
                height: 100px;
                font-size: 40px;
            }
            
            .call-status,
            .incoming-call-status {
                font-size: 20px;
            }
            
            .call-timer,
            .incoming-call-user {
                font-size: 16px;
            }
            
            .call-btn {
                width: 50px;
                height: 50px;
            }
            
            .call-icon {
                width: 20px;
                height: 20px;
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
                <button class="action-btn" id="callBtn" title="Voice Call">
                    <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"></path>
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
    
    <!-- Call Modal -->
    <div class="call-modal" id="callModal">
        <div class="call-container">
            <div class="call-avatar" id="callAvatar">👤</div>
            <div class="call-status" id="callStatus">Calling...</div>
            <div class="call-timer" id="callTimer">00:00</div>
            <div class="call-actions">
                <button class="call-btn mute" id="muteBtn" title="Mute/Unmute">
                    <svg class="call-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"></path>
                    </svg>
                </button>
                <button class="call-btn end" id="endCallBtn" title="End Call">
                    <svg class="call-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 8l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2M5 3a2 2 0 00-2 2v1c0 8.284 6.716 15 15 15h1a2 2 0 002-2v-3.28a1 1 0 00-.684-.948l-4.493-1.498a1 1 0 00-1.21.502l-1.13 2.257a11.042 11.042 0 01-5.516-5.517l2.257-1.128a1 1 0 00.502-1.21L9.228 3.683A1 1 0 008.279 3H5z"></path>
                    </svg>
                </button>
            </div>
        </div>
    </div>
    
    <!-- Incoming Call Modal -->
    <div class="incoming-call-modal" id="incomingCallModal">
        <div class="incoming-call-container">
            <div class="incoming-call-avatar" id="incomingCallAvatar">👤</div>
            <div class="incoming-call-status">Incoming Call</div>
            <div class="incoming-call-user" id="incomingCallUser">User</div>
            <div class="incoming-call-actions">
                <button class="call-btn reject" id="rejectCallBtn" title="Reject">
                    <svg class="call-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
                <button class="call-btn answer" id="answerCallBtn" title="Answer">
                    <svg class="call-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"></path>
                    </svg>
                </button>
            </div>
        </div>
    </div>
    
    <!-- User Select Modal -->
    <div class="user-select-modal" id="userSelectModal">
        <div class="user-select-container">
            <div class="user-select-title">Select User to Call</div>
            <div class="user-list" id="userList">
                <!-- User list will be populated here -->
            </div>
            <button class="cancel-btn" id="cancelCallBtn">Cancel</button>
        </div>
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
        
        // WebRTC variables
        var localStream;
        var remoteStream;
        var peerConnection;
        var isInCall = false;
        var isMuted = false;
        var callTimer;
        var callSeconds = 0;
        var callPartner = "";
        
        // WebRTC configuration
        const configuration = {
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' }
            ]
        };
        
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
        
        // Function to format call timer
        function formatCallTimer(seconds) {
            const mins = Math.floor(seconds / 60);
            const secs = seconds % 60;
            return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
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
            } else if (msg.type === "call") {
                const callIcon = msg.text.includes("started") ? "📞" : "📵";
                messageContent = `<div style="display: flex; align-items: center; gap: 8px;">
                    <span>${callIcon}</span>
                    <span>${msg.text}</span>
                </div>`;
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
        
        // Function to populate user list for calling
        function populateUserList() {
            const userList = document.getElementById("userList");
            userList.innerHTML = '';
            
            online_users.forEach(user => {
                if (user !== username) {
                    const userItem = document.createElement("div");
                    userItem.className = "user-item";
                    userItem.innerHTML = `
                        <div class="user-item-avatar">${user.charAt(0).toUpperCase()}</div>
                        <div class="user-item-name">${user}</div>
                        <div class="user-item-status"></div>
                    `;
                    userItem.addEventListener("click", function() {
                        initiateCall(user);
                    });
                    userList.appendChild(userItem);
                }
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
        
        // Function to show notification
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
        
        // WebRTC functions
        async function initializeMedia() {
            try {
                localStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
                return localStream;
            } catch (error) {
                console.error('Error accessing media devices:', error);
                showNotification("Could not access microphone");
                return null;
            }
        }
        
        function createPeerConnection() {
            try {
                peerConnection = new RTCPeerConnection(configuration);
                
                // Add local stream to peer connection
                if (localStream) {
                    localStream.getTracks().forEach(track => {
                        peerConnection.addTrack(track, localStream);
                    });
                }
                
                // Handle remote stream
                peerConnection.ontrack = (event) => {
                    remoteStream = event.streams[0];
                    // Play remote audio
                    const audio = new Audio();
                    audio.srcObject = remoteStream;
                    audio.play();
                };
                
                // Handle ICE candidates
                peerConnection.onicecandidate = (event) => {
                    if (event.candidate) {
                        socket.emit('ice_candidate', {
                            candidate: event.candidate,
                            to: callPartner
                        });
                    }
                };
                
                return peerConnection;
            } catch (error) {
                console.error('Error creating peer connection:', error);
                return null;
            }
        }
        
        async function initiateCall(targetUser) {
            if (isInCall) {
                showNotification("You are already in a call");
                return;
            }
            
            callPartner = targetUser;
            
            // Initialize media
            localStream = await initializeMedia();
            if (!localStream) {
                return;
            }
            
            // Create peer connection
            peerConnection = createPeerConnection();
            if (!peerConnection) {
                return;
            }
            
            // Create offer
            const offer = await peerConnection.createOffer();
            await peerConnection.setLocalDescription(offer);
            
            // Send offer to target user
            socket.emit('call_offer', {
                offer: offer,
                to: targetUser,
                from: username
            });
            
            // Show call modal
            document.getElementById("callModal").style.display = "flex";
            document.getElementById("callStatus").textContent = `Calling ${targetUser}...`;
            document.getElementById("callAvatar").textContent = targetUser.charAt(0).toUpperCase();
            
            // Start call timer
            startCallTimer();
            
            // Add call message to chat
            const now = new Date();
            const messageId = "msg_" + Date.now() + "_" + Math.random().toString(36).substr(2, 9);
            socket.send({
                id: messageId,
                user: username, 
                text: `Voice call started with ${targetUser}`,
                datetime: now.toISOString(),
                type: "call",
                status: "sent"
            });
        }
        
        async function acceptCall() {
            // Initialize media
            localStream = await initializeMedia();
            if (!localStream) {
                return;
            }
            
            // Create peer connection
            peerConnection = createPeerConnection();
            if (!peerConnection) {
                return;
            }
            
            // Hide incoming call modal
            document.getElementById("incomingCallModal").style.display = "none";
            
            // Show call modal
            document.getElementById("callModal").style.display = "flex";
            document.getElementById("callStatus").textContent = `Connected with ${callPartner}`;
            document.getElementById("callAvatar").textContent = callPartner.charAt(0).toUpperCase();
            
            // Start call timer
            startCallTimer();
            
            // Add call message to chat
            const now = new Date();
            const messageId = "msg_" + Date.now() + "_" + Math.random().toString(36).substr(2, 9);
            socket.send({
                id: messageId,
                user: username, 
                text: `Voice call with ${callPartner} accepted`,
                datetime: now.toISOString(),
                type: "call",
                status: "sent"
            });
        }
        
        function rejectCall() {
            // Send reject signal
            socket.emit('call_rejected', {
                to: callPartner,
                from: username
            });
            
            // Hide incoming call modal
            document.getElementById("incomingCallModal").style.display = "none";
            
            // Add call message to chat
            const now = new Date();
            const messageId = "msg_" + Date.now() + "_" + Math.random().toString(36).substr(2, 9);
            socket.send({
                id: messageId,
                user: username, 
                text: `Voice call from ${callPartner} rejected`,
                datetime: now.toISOString(),
                type: "call",
                status: "sent"
            });
            
            callPartner = "";
        }
        
        function endCall() {
            // Stop local stream
            if (localStream) {
                localStream.getTracks().forEach(track => track.stop());
                localStream = null;
            }
            
            // Close peer connection
            if (peerConnection) {
                peerConnection.close();
                peerConnection = null;
            }
            
            // Send end call signal
            if (callPartner) {
                socket.emit('call_ended', {
                    to: callPartner,
                    from: username
                });
            }
            
            // Hide call modal
            document.getElementById("callModal").style.display = "none";
            
            // Stop call timer
            stopCallTimer();
            
            // Add call message to chat
            if (callPartner) {
                const now = new Date();
                const messageId = "msg_" + Date.now() + "_" + Math.random().toString(36).substr(2, 9);
                socket.send({
                    id: messageId,
                    user: username, 
                    text: `Voice call with ${callPartner} ended (${formatCallTimer(callSeconds)})`,
                    datetime: now.toISOString(),
                    type: "call",
                    status: "sent"
                });
            }
            
            isInCall = false;
            callPartner = "";
            callSeconds = 0;
        }
        
        function toggleMute() {
            if (localStream) {
                const audioTrack = localStream.getAudioTracks()[0];
                if (audioTrack) {
                    audioTrack.enabled = !audioTrack.enabled;
                    isMuted = !audioTrack.enabled;
                    
                    // Update UI
                    const muteBtn = document.getElementById("muteBtn");
                    if (isMuted) {
                        muteBtn.classList.add("muted");
                        muteBtn.innerHTML = `
                            <svg class="call-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" clip-rule="evenodd"></path>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2"></path>
                            </svg>
                        `;
                    } else {
                        muteBtn.classList.remove("muted");
                        muteBtn.innerHTML = `
                            <svg class="call-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"></path>
                            </svg>
                        `;
                    }
                }
            }
        }
        
        function startCallTimer() {
            callSeconds = 0;
            isInCall = true;
            document.getElementById("callBtn").classList.add("calling");
            
            callTimer = setInterval(() => {
                callSeconds++;
                document.getElementById("callTimer").textContent = formatCallTimer(callSeconds);
            }, 1000);
        }
        
        function stopCallTimer() {
            clearInterval(callTimer);
            document.getElementById("callBtn").classList.remove("calling");
        }
        
        // Socket event handlers
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
            
            // End call if user was in call with the user who left
            if (isInCall && callPartner === data.user) {
                endCall();
                showNotification(`${data.user} ended the call`);
            }
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
        
        // WebRTC Socket Event Handlers
        socket.on("call_offer", async function(data) {
            if (isInCall) {
                // Reject call if already in a call
                socket.emit('call_rejected', {
                    to: data.from,
                    from: username
                });
                return;
            }
            
            callPartner = data.from;
            
            // Show incoming call modal
            document.getElementById("incomingCallModal").style.display = "flex";
            document.getElementById("incomingCallUser").textContent = data.from;
            document.getElementById("incomingCallAvatar").textContent = data.from.charAt(0).toUpperCase();
        });
        
        socket.on("call_answer", async function(data) {
            if (!peerConnection) return;
            
            // Set remote description
            await peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer));
            
            // Update call status
            document.getElementById("callStatus").textContent = `Connected with ${callPartner}`;
        });
        
        socket.on("call_rejected", function(data) {
            // Hide call modal
            document.getElementById("callModal").style.display = "none";
            
            // Stop call timer
            stopCallTimer();
            
            // Show notification
            showNotification(`${data.from} rejected your call`);
            
            // Add call message to chat
            const now = new Date();
            const messageId = "msg_" + Date.now() + "_" + Math.random().toString(36).substr(2, 9);
            socket.send({
                id: messageId,
                user: username, 
                text: `Voice call with ${data.from} rejected`,
                datetime: now.toISOString(),
                type: "call",
                status: "sent"
            });
            
            // Clean up
            if (localStream) {
                localStream.getTracks().forEach(track => track.stop());
                localStream = null;
            }
            
            if (peerConnection) {
                peerConnection.close();
                peerConnection = null;
            }
            
            isInCall = false;
            callPartner = "";
        });
        
        socket.on("call_ended", function(data) {
            // Hide call modal
            document.getElementById("callModal").style.display = "none";
            
            // Stop call timer
            stopCallTimer();
            
            // Show notification
            showNotification(`${data.from} ended the call`);
            
            // Add call message to chat
            const now = new Date();
            const messageId = "msg_" + Date.now() + "_" + Math.random().toString(36).substr(2, 9);
            socket.send({
                id: messageId,
                user: username, 
                text: `Voice call with ${data.from} ended (${formatCallTimer(callSeconds)})`,
                datetime: now.toISOString(),
                type: "call",
                status: "sent"
            });
            
            // Clean up
            if (localStream) {
                localStream.getTracks().forEach(track => track.stop());
                localStream = null;
            }
            
            if (peerConnection) {
                peerConnection.close();
                peerConnection = null;
            }
            
            isInCall = false;
            callPartner = "";
        });
        
        socket.on("ice_candidate", async function(data) {
            if (!peerConnection) return;
            
            try {
                await peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
            } catch (error) {
                console.error('Error adding ICE candidate:', error);
            }
        });
        
        // UI Event Handlers
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
        
        // Call button event handler - Fixed with proper event listener
        document.addEventListener('DOMContentLoaded', function() {
            const callBtn = document.getElementById("callBtn");
            if (callBtn) {
                console.log("Call button found, adding event listener");
                callBtn.addEventListener("click", function() {
                    console.log("Call button clicked!");
                    
                    if (!username) {
                        username = document.getElementById("user").value;
                        if (!username) {
                            showNotification("Please enter your name first!");
                            return;
                        }
                        // Notify server that user is online
                        socket.emit("user_online", { user: username });
                    }
                    
                    if (isInCall) {
                        endCall();
                    } else {
                        // Show user select modal
                        populateUserList();
                        document.getElementById("userSelectModal").style.display = "flex";
                    }
                });
            } else {
                console.error("Call button not found in DOM!");
            }
        });
        
        // Answer call button event handler
        document.getElementById("answerCallBtn").addEventListener("click", function() {
            acceptCall();
        });
        
        // Reject call button event handler
        document.getElementById("rejectCallBtn").addEventListener("click", function() {
            rejectCall();
        });
        
        // End call button event handler
        document.getElementById("endCallBtn").addEventListener("click", function() {
            endCall();
        });
        
        // Mute button event handler
        document.getElementById("muteBtn").addEventListener("click", function() {
            toggleMute();
        });
        
        // Cancel call button event handler
        document.getElementById("cancelCallBtn").addEventListener("click", function() {
            document.getElementById("userSelectModal").style.display = "none";
        });
        
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

# WebRTC call event handlers
@socketio.on("call_offer")
def handle_call_offer(data):
    target_user = data.get('to')
    if target_user:
        # Find the session ID of the target user
        target_sid = None
        for sid, user in session_to_user.items():
            if user == target_user:
                target_sid = sid
                break
        
        if target_sid:
            # Forward the offer to the target user
            emit("call_offer", data, room=target_sid)

@socketio.on("call_answer")
def handle_call_answer(data):
    target_user = data.get('to')
    if target_user:
        # Find the session ID of the target user
        target_sid = None
        for sid, user in session_to_user.items():
            if user == target_user:
                target_sid = sid
                break
        
        if target_sid:
            # Forward the answer to the target user
            emit("call_answer", data, room=target_sid)

@socketio.on("call_rejected")
def handle_call_rejected(data):
    target_user = data.get('to')
    if target_user:
        # Find the session ID of the target user
        target_sid = None
        for sid, user in session_to_user.items():
            if user == target_user:
                target_sid = sid
                break
        
        if target_sid:
            # Forward the rejection to the target user
            emit("call_rejected", data, room=target_sid)

@socketio.on("call_ended")
def handle_call_ended(data):
    target_user = data.get('to')
    if target_user:
        # Find the session ID of the target user
        target_sid = None
        for sid, user in session_to_user.items():
            if user == target_user:
                target_sid = sid
                break
        
        if target_sid:
            # Forward the end call signal to the target user
            emit("call_ended", data, room=target_sid)

@socketio.on("ice_candidate")
def handle_ice_candidate(data):
    target_user = data.get('to')
    if target_user:
        # Find the session ID of the target user
        target_sid = None
        for sid, user in session_to_user.items():
            if user == target_user:
                target_sid = sid
                break
        
        if target_sid:
            # Forward the ICE candidate to the target user
            emit("ice_candidate", data, room=target_sid)

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
        
        # Clean up any active calls
        if username in user_call_partner:
            partner = user_call_partner[username]
            del user_call_partner[username]
            if partner in user_call_partner and user_call_partner[partner] == username:
                del user_call_partner[partner]
                
                # Notify the partner that the call ended
                partner_sid = None
                for sid, user in session_to_user.items():
                    if user == partner:
                        partner_sid = sid
                        break
                
                if partner_sid:
                    emit("call_ended", {"from": username}, room=partner_sid)

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
