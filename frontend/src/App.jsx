import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  MessageSquare, 
  Map as MapIcon, 
  User, 
  Scroll, 
  Settings, 
  Send,
  MoreVertical,
  Menu,
  X
} from 'lucide-react';
import './App.css';

const API_URL = 'http://localhost:8000/api';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // Initialize game
    const initGame = async () => {
      try {
        await axios.post(`${API_URL}/init`, {
          player_name: "Henry",
          story_dir: "Pirate Adventure"
        });
        // Add welcome message
        setMessages([{
          character: "System",
          content: "Welcome to RoleRealm! You are Henry. You are aboard the Sea Serpent with Captain Morgan, Marina, and Jack. The Dungeon Master 'Martin' is watching.",
          type: "system",
          timestamp: new Date().toISOString()
        }]);
      } catch (error) {
        console.error("Failed to init game:", error);
      }
    };
    initGame();
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = {
      character: "Henry",
      content: input,
      type: "message",
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_URL}/chat`, { message: userMsg.content });
      if (response.data.messages) {
        setMessages(prev => [...prev, ...response.data.messages]);
      }
    } catch (error) {
      console.error("Error sending message:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <div className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="logo-area">
          <span className="logo-icon">🎲</span>
          {sidebarOpen && <h1 className="logo-text">Metavern</h1>}
        </div>
        
        <nav className="nav-menu">
          <NavItem icon={<MessageSquare />} label="Play" active />
          <NavItem icon={<MapIcon />} label="World" />
          <NavItem icon={<User />} label="Character Sheet" />
          <NavItem icon={<Scroll />} label="Quests" badge="Searching" />
          <NavItem icon={<Settings />} label="Settings" />
        </nav>

        <div className="user-profile">
          <div className="avatar">H</div>
          {sidebarOpen && (
            <div className="user-info">
              <span className="user-name">Henry</span>
              <span className="user-status">Legend</span>
            </div>
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="main-content">
        <header className="chat-header">
          <button className="toggle-sidebar" onClick={() => setSidebarOpen(!sidebarOpen)}>
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          <h2>Aboard the Sea Serpent</h2>
          <div className="header-actions">
            <span className="location-coords">Current Location (160, 347)</span>
          </div>
        </header>

        <div className="messages-area">
          {messages.map((msg, idx) => (
            <MessageBubble key={idx} message={msg} />
          ))}
          {isLoading && (
            <div className="typing-indicator">
              <span>Thinking...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-area">
          <form onSubmit={handleSend} className="message-form">
            <input 
              type="text" 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Say something... (Use @Martin to ask the DM)"
              disabled={isLoading}
            />
            <button type="submit" disabled={isLoading || !input.trim()}>
              <Send size={20} />
            </button>
          </form>
          <div className="input-footer">
            Metavern is in early access beta.
          </div>
        </div>
      </div>

      {/* Right Info Panel */}
      <div className="info-panel">
        <div className="location-card">
          <h3>Sea Serpent Deck</h3>
          <p className="location-desc">
            The sun is setting over the endless ocean. The black sails billow in the breeze.
          </p>
          <div className="location-image-placeholder">
            🌊 Ship Deck
          </div>
          <button className="secondary-btn">Change location</button>
        </div>

        <div className="npc-list">
          <h3>Nearby NPCs</h3>
          <NPCItem name="Captain Morgan" role="Pirate Captain" status="Commanding" />
          <NPCItem name="Marina" role="Navigator" status="Charting" />
          <NPCItem name="Jack" role="Gunner" status="Cleaning" />
          <NPCItem name="Martin" role="Dungeon Master" status="Observing" special />
        </div>
      </div>
    </div>
  );
}

const NavItem = ({ icon, label, active, badge }) => (
  <div className={`nav-item ${active ? 'active' : ''}`}>
    {icon}
    <span className="nav-label">{label}</span>
    {badge && <span className="nav-badge">{badge}</span>}
  </div>
);

const MessageBubble = ({ message }) => {
  const isUser = message.character === "Henry";
  const isSystem = message.type === "system";
  const isAction = message.type === "action";
  const isDM = message.character === "Martin";

  if (isSystem) {
    return <div className="system-message">{message.content}</div>;
  }

  return (
    <div className={`message-bubble ${isUser ? 'user' : 'ai'} ${isDM ? 'dm' : ''}`}>
      <div className="message-avatar">
        {message.character[0]}
      </div>
      <div className="message-content-wrapper">
        <div className="message-header">
          <span className="character-name">{message.character}</span>
          <MoreVertical size={16} className="message-options" />
        </div>
        <div className="message-text">
          {isAction ? <i>*{message.content}*</i> : message.content}
        </div>
        {message.action && !isAction && (
          <div className="message-action">*{message.action}*</div>
        )}
      </div>
    </div>
  );
};

const NPCItem = ({ name, role, status, special }) => (
  <div className={`npc-item ${special ? 'special' : ''}`}>
    <div className="npc-avatar">{name[0]}</div>
    <div className="npc-info">
      <span className="npc-name">{name}</span>
      <span className="npc-role">{role}</span>
    </div>
    <div className="npc-status-dot" title={status} />
  </div>
);

export default App;
