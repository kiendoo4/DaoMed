import { useEffect, useState, useRef } from 'react';
import { List, Input, Button, Spin, message, Avatar, Empty, Tag } from 'antd';
import { SendOutlined, UserOutlined, RobotOutlined, SearchOutlined } from '@ant-design/icons';
import api from '../api';
import RAGDetailsModal from './RAGDetailsModal';

// Simple markdown renderer for bold text
const renderMarkdown = (text) => {
  if (!text) return '';
  
  // Replace **text** with <strong>text</strong>
  const boldText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  // Replace line breaks with <br>
  const withLineBreaks = boldText.replace(/\n/g, '<br />');
  
  return withLineBreaks;
};

export default function ChatWindow({ dialogId, onMessageSent }) {
  const [messages, setMessages] = useState([]);
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [ragModalVisible, setRagModalVisible] = useState(false);
  const [selectedRagDetails, setSelectedRagDetails] = useState(null);
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);

  useEffect(() => {
    if (dialogId) {
      fetchMessages();
    }
  }, [dialogId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    if (messagesContainerRef.current) {
      setTimeout(() => {
        messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
      }, 100); // Delay nhỏ để đảm bảo content đã render
    }
  };

  const fetchMessages = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/dialog/${dialogId}/messages`);
      
      console.log('Messages response:', response.data);
      setMessages(response.data.messages || []);
    } catch (err) {
      console.error('Error fetching messages:', err);
      message.error('Failed to load messages');
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!content.trim() || sending) return;

    const userMessage = {
      role: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString()
    };

    // Add user message immediately
    setMessages(prev => [...prev, userMessage]);
    setContent('');
    
    // Gọi callback để cập nhật DialogList ngay khi user nhắn
    if (onMessageSent) onMessageSent();
    
    // Add loading message for bot
    const loadingMessage = {
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      loading: true
    };
    
    setMessages(prev => [...prev, loadingMessage]);

    try {
      setSending(true);
      
      const response = await api.post(`/api/dialog/${dialogId}/chat`, {
        message: userMessage.content
      });
      
      console.log('Send message response:', response.data);
      
      // Replace loading message with actual response
      const botMessage = {
        role: 'assistant',
        content: response.data.bot_response.content,
        timestamp: response.data.bot_response.timestamp,
        loading: false,
        ragDetails: response.data.rag_details || null
      };
      
      setMessages(prev => prev.map(msg => 
        msg.loading ? botMessage : msg
      ));
      
      // Gọi callback để cập nhật DialogList khi bot trả lời
      if (onMessageSent) onMessageSent();
      
    } catch (err) {
      console.error('Error sending message:', err);
      message.error('Failed to send message');
      
      // Remove loading message on error
      setMessages(prev => prev.filter(msg => !msg.loading));
    } finally {
      setSending(false);
    }
  };

  const formatTime = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleTimeString('vi-VN', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const showRAGDetails = (ragDetails) => {
    setSelectedRagDetails(ragDetails);
    setRagModalVisible(true);
  };

  const closeRAGModal = () => {
    setRagModalVisible(false);
    setSelectedRagDetails(null);
  };

  if (!dialogId) {
    return (
      <div style={{ 
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '40px'
      }}>
        <Empty
          image={<RobotOutlined style={{ fontSize: '64px', color: '#d9d9d9' }} />}
          description={
            <span style={{ fontSize: '16px', color: '#666' }}>
              Chọn dialog để bắt đầu chat với Knowledge Base
            </span>
          }
        />
      </div>
    );
  }

  return (
    <div style={{ 
      height: '100%', 
      display: 'flex', 
      flexDirection: 'column'
    }}>
      {/* Messages Area */}
      <div 
        ref={messagesContainerRef}
        style={{ 
          flex: 1, 
          overflowY: 'auto', 
          overflowX: 'hidden',
          padding: '20px',
          backgroundColor: '#fafafa',
          scrollBehavior: 'smooth',
          minHeight: 0, // Quan trọng cho flex child
          maxHeight: '100%' // Đảm bảo không vượt quá container
        }}
      >
        {loading ? (
          <div style={{ 
            textAlign: 'center', 
            padding: '40px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '16px'
          }}>
            <Spin size="large" />
            <span style={{ color: '#666' }}>Loading messages...</span>
          </div>
        ) : messages.length === 0 ? (
          <div style={{ 
            textAlign: 'center', 
            padding: '40px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '16px'
          }}>
            <RobotOutlined style={{ fontSize: '48px', color: '#d9d9d9' }} />
            <span style={{ color: '#666', fontSize: '16px' }}>
              Bắt đầu cuộc trò chuyện với Knowledge Base
            </span>
          </div>
        ) : (
          <div style={{ 
            maxWidth: '800px', 
            margin: '0 auto',
            paddingBottom: '20px' // Thêm padding bottom để có space scroll
          }}>
            {messages.map((item, index) => (
              <div
                key={index}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '12px',
                  marginBottom: '16px',
                  justifyContent: item.role === 'user' ? 'flex-end' : 'flex-start'
                }}
              >
                {item.role === 'assistant' && (
                  <Avatar 
                    icon={<RobotOutlined />}
                    style={{ 
                      backgroundColor: '#52c41a',
                      flexShrink: 0,
                      marginTop: '4px'
                    }}
                  />
                )}
                
                <div style={{
                  maxWidth: '70%',
                  backgroundColor: item.role === 'user' ? '#1890ff' : '#fff',
                  color: item.role === 'user' ? '#fff' : '#000',
                  padding: '12px 16px',
                  borderRadius: '18px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                  wordBreak: 'break-word',
                  whiteSpace: 'pre-wrap',
                  overflowWrap: 'break-word',
                  hyphens: 'auto'
                }}>
                  {item.loading ? (
                    <div style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '8px',
                      minHeight: '20px'
                    }}>
                      <Spin size="small" />
                      <span style={{ fontSize: '14px', color: '#666' }}>
                        AI đang suy nghĩ...
                      </span>
                    </div>
                  ) : (
                    <>
                      <div 
                        style={{ 
                          fontSize: '14px', 
                          lineHeight: '1.6',
                          color: item.role === 'user' ? '#fff' : '#000'
                        }}
                        dangerouslySetInnerHTML={{ 
                          __html: item.role === 'assistant' 
                            ? renderMarkdown(item.content) 
                            : item.content 
                        }}
                      />
                      
                      {/* RAG Details Button for Assistant Messages */}
                      {item.role === 'assistant' && item.ragDetails && (
                        <div style={{ 
                          marginTop: '8px', 
                          display: 'flex', 
                          alignItems: 'center', 
                          gap: '8px',
                          flexWrap: 'wrap'
                        }}>
                          <Button
                            type="text"
                            size="small"
                            icon={<SearchOutlined />}
                            onClick={() => showRAGDetails(item.ragDetails)}
                            style={{ 
                              padding: '2px 8px', 
                              height: 'auto',
                              fontSize: '12px',
                              color: '#52c41a'
                            }}
                          >
                            Xem RAG Details
                          </Button>
                          
                          <Tag color="green" size="small">
                            RAG: {item.ragDetails.chunks_used?.length || 0} chunks
                          </Tag>
                        </div>
                      )}
                    </>
                  )}
                  <div style={{ 
                    fontSize: '11px', 
                    opacity: 0.7, 
                    marginTop: '4px',
                    textAlign: item.role === 'user' ? 'right' : 'left'
                  }}>
                    {formatTime(item.timestamp)}
                  </div>
                </div>
                
                {item.role === 'user' && (
                  <Avatar 
                    icon={<UserOutlined />}
                    style={{ 
                      backgroundColor: '#1890ff',
                      flexShrink: 0,
                      marginTop: '4px'
                    }}
                  />
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div style={{ 
        padding: '20px',
        backgroundColor: '#fff',
        borderTop: '1px solid #f0f0f0',
        flexShrink: 0
      }}>
        <div style={{ 
          maxWidth: '800px', 
          margin: '0 auto',
          display: 'flex', 
          gap: '12px',
          alignItems: 'flex-end'
        }}>
          <Input.TextArea
            value={content}
            onChange={e => setContent(e.target.value)}
            onPressEnter={(e) => {
              if (!e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
            placeholder="Nhập tin nhắn... (Shift + Enter để xuống dòng)"
            disabled={sending}
            style={{ 
              flex: 1,
              resize: 'none',
              borderRadius: '20px',
              padding: '12px 16px',
              fontSize: '14px',
              lineHeight: '1.5',
              minHeight: '44px',
              maxHeight: '120px'
            }}
            autoSize={{ minRows: 1, maxRows: 4 }}
          />
          <Button 
            type="primary" 
            icon={<SendOutlined />}
            onClick={sendMessage}
            loading={sending}
            disabled={!content.trim()}
            style={{
              borderRadius: '50%',
              width: '44px',
              height: '44px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          />
        </div>
      </div>
      
      {/* RAG Details Modal */}
      <RAGDetailsModal
        visible={ragModalVisible}
        onClose={closeRAGModal}
        ragDetails={selectedRagDetails}
      />
    </div>
  );
} 