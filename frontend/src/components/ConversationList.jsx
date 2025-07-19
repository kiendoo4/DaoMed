import { useEffect, useState } from 'react';
import { List, Button, message, Spin, Modal, Input } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import axios from 'axios';

export default function ConversationList({ onSelect, selectedId }) {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [newTopic, setNewTopic] = useState('');

  useEffect(() => {
    fetchConversations();
  }, []);

  const fetchConversations = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.get('/api/chat/conversations', {
        withCredentials: true,
        timeout: 30000
      });
      
      console.log('Conversations response:', response.data);
      setConversations(response.data.conversations || []);
    } catch (err) {
      console.error('Error fetching conversations:', err);
      setError(err.message);
      message.error(`Failed to load conversations: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const createConversation = async () => {
    if (!newTopic.trim()) {
      message.error('Vui lòng nhập chủ đề conversation');
      return;
    }

    try {
      const response = await axios.post('/api/chat/conversations', {
        topic: newTopic.trim()
      }, {
        withCredentials: true,
        timeout: 30000
      });
      
      console.log('Create conversation response:', response.data);
      setConversations([response.data.conversation, ...conversations]);
      setCreateModalVisible(false);
      setNewTopic('');
      message.success('Conversation created successfully!');
    } catch (err) {
      console.error('Error creating conversation:', err);
      message.error(`Failed to create conversation: ${err.message}`);
    }
  };

  const deleteConversation = async (conversationId) => {
    try {
      await axios.delete(`/api/chat/conversations/${conversationId}`, {
        withCredentials: true,
        timeout: 30000
      });
      
      setConversations(conversations.filter(conv => conv.id !== conversationId));
      if (selectedId === conversationId) {
        onSelect(null);
      }
      message.success('Conversation deleted successfully!');
    } catch (err) {
      console.error('Error deleting conversation:', err);
      message.error(`Failed to delete conversation: ${err.message}`);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleString('vi-VN');
  };

  if (loading) {
    return <Spin size="large" tip="Loading conversations..." />;
  }

  if (error) {
    return (
      <div style={{ color: 'red', padding: '16px' }}>
        Error loading conversations: {error}
      </div>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: '16px' }}>
        <Button 
          type="primary" 
          icon={<PlusOutlined />}
          onClick={() => setCreateModalVisible(true)}
          block
        >
          Tạo Conversation
        </Button>
      </div>
      
      <List
        dataSource={conversations}
        renderItem={item => (
          <List.Item 
            onClick={() => onSelect(item.id)} 
            style={{ 
              cursor: 'pointer',
              backgroundColor: selectedId === item.id ? '#f0f0f0' : 'transparent',
              padding: '8px 12px',
              margin: '4px 0',
              borderRadius: '4px',
              border: selectedId === item.id ? '1px solid #1890ff' : '1px solid transparent'
            }}
            actions={[
              <Button 
                type="text" 
                danger 
                icon={<DeleteOutlined />}
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  deleteConversation(item.id);
                }}
              />
            ]}
          >
            <List.Item.Meta
              title={item.topic || 'Untitled Conversation'}
              description={
                <div>
                  <div>Dialogs: {item.dialog_count || 0}</div>
                  <div>Created: {formatDate(item.started_at)}</div>
                  {item.last_dialog_at && (
                    <div>Last activity: {formatDate(item.last_dialog_at)}</div>
                  )}
                </div>
              }
            />
          </List.Item>
        )}
        locale={{ emptyText: 'Chưa có conversations nào' }}
      />

      <Modal
        title="Tạo Conversation Mới"
        open={createModalVisible}
        onOk={createConversation}
        onCancel={() => {
          setCreateModalVisible(false);
          setNewTopic('');
        }}
        okText="Tạo"
        cancelText="Hủy"
      >
        <Input
          placeholder="Nhập chủ đề conversation..."
          value={newTopic}
          onChange={(e) => setNewTopic(e.target.value)}
          onPressEnter={createConversation}
        />
      </Modal>
    </div>
  );
} 