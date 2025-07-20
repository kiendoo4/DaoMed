import { useEffect, useState } from 'react';
import { List, Button, Modal, Input, message, Spin } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import api from '../api';

export default function DialogList({ onSelect, selectedId, reloadKey }) {
  const [dialogs, setDialogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [newName, setNewName] = useState('');
  const [creatingDialog, setCreatingDialog] = useState(false);

  useEffect(() => {
    fetchDialogs();
  }, [reloadKey]);

  const fetchDialogs = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Lấy tất cả dialogs của user (không cần conversation)
      const response = await api.get('/api/chat/dialogs');
      
      console.log('Dialogs response:', response.data);
      setDialogs(response.data.dialogs || []);
    } catch (err) {
      console.error('Error fetching dialogs:', err);
      setError(err.message);
      message.error(`Failed to load dialogs: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const createDialog = async () => {
    if (!newName.trim()) {
      message.error('Vui lòng nhập tên dialog');
      return;
    }

    try {
      setCreatingDialog(true);
      console.log('Creating dialog with name:', newName.trim());
      
      // Tạo dialog trực tiếp (không cần conversation)
      const response = await api.post('/api/chat/dialogs', {
        name: newName.trim()
      });
      
      console.log('Create dialog response:', response.data);
      const newDialog = response.data.dialog;
      
      // Đóng modal trước
      resetModal();
      
      // Cập nhật danh sách dialogs
      setDialogs([newDialog, ...dialogs]);
      
      // Tự động chọn dialog mới tạo
      onSelect(newDialog.id);
      
      message.success('Dialog created successfully!');
    } catch (err) {
      console.error('Error creating dialog:', err);
      message.error(`Failed to create dialog: ${err.message}`);
    } finally {
      setCreatingDialog(false);
    }
  };

  const deleteDialog = async (dialogId) => {
    try {
      await api.delete(`/api/chat/dialogs/${dialogId}`);
      
      setDialogs(dialogs.filter(d => d.id !== dialogId));
      if (selectedId === dialogId) {
        onSelect(null);
      }
      message.success('Dialog deleted successfully!');
    } catch (err) {
      console.error('Error deleting dialog:', err);
      message.error(`Failed to delete dialog: ${err.message}`);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleString('vi-VN');
  };

  const resetModal = () => {
    setCreateModalVisible(false);
    setNewName('');
  };

  if (loading) {
    return <Spin size="large" tip="Loading dialogs..." />;
  }

  if (error) {
    return (
      <div style={{ color: 'red', padding: '16px' }}>
        Error loading dialogs: {error}
      </div>
    );
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Create Button */}
      <div style={{ marginBottom: '16px', flexShrink: 0 }}>
        <Button 
          type="primary" 
          icon={<PlusOutlined />}
          onClick={() => setCreateModalVisible(true)}
          block
        >
          Tạo Dialog
        </Button>
      </div>
      
      {/* Dialog List */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        <List
          dataSource={dialogs}
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
                    deleteDialog(item.id);
                  }}
                />
              ]}
            >
              <List.Item.Meta
                title={item.name || 'Untitled Dialog'}
                description={
                  <div>
                    <div>Messages: {item.message_count || 0}</div>
                    <div>Created: {formatDate(item.created_at)}</div>
                    {item.last_message_at && (
                      <div>Last message: {formatDate(item.last_message_at)}</div>
                    )}
                  </div>
                }
              />
            </List.Item>
          )}
          locale={{ emptyText: 'Chưa có dialogs nào' }}
        />
      </div>

      <Modal
        title="Tạo Dialog Mới"
        open={createModalVisible}
        onOk={createDialog}
        onCancel={resetModal}
        okText="Tạo"
        cancelText="Hủy"
        destroyOnClose={true}
        maskClosable={false}
        keyboard={false}
        confirmLoading={creatingDialog}
      >
        <Input
          placeholder="Nhập tên dialog..."
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onPressEnter={createDialog}
          autoFocus
        />
      </Modal>
    </div>
  );
} 