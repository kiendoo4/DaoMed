import React from 'react';
import { Modal, Table, Tag, Typography, Divider, Space } from 'antd';
import { SearchOutlined, FileTextOutlined, DatabaseOutlined } from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;

export default function RAGDetailsModal({ visible, onClose, ragDetails }) {
  if (!ragDetails) return null;

  const columns = [
    {
      title: 'Chunk ID',
      dataIndex: 'metadata',
      key: 'chunk_id',
      render: (metadata) => metadata?.chunk_id || 'N/A',
      width: 100,
    },
    {
      title: 'KB ID',
      dataIndex: 'metadata',
      key: 'kb_id',
      render: (metadata) => `KB_${metadata?.kb_id || 'N/A'}`,
      width: 100,
    },
    {
      title: 'Row Index',
      dataIndex: 'metadata',
      key: 'row_index',
      render: (metadata) => metadata?.row_index || 'N/A',
      width: 100,
    },
    {
      title: 'Cosine Score',
      dataIndex: 'score',
      key: 'score',
      render: (score) => (
        <Tag color={score >= 0.8 ? 'green' : score >= 0.6 ? 'orange' : 'red'}>
          {score.toFixed(3)}
        </Tag>
      ),
      width: 120,
      sorter: (a, b) => a.score - b.score,
      defaultSortOrder: 'descend',
    },
    {
      title: 'Content',
      dataIndex: 'content',
      key: 'content',
      render: (content) => (
        <div style={{ 
          maxWidth: '400px', 
          maxHeight: '100px', 
          overflow: 'auto',
          fontSize: '12px',
          lineHeight: '1.4',
          fontFamily: 'monospace',
          backgroundColor: '#f5f5f5',
          padding: '8px',
          borderRadius: '4px',
          border: '1px solid #d9d9d9'
        }}>
          {content}
        </div>
      ),
    },
  ];

  const dataSource = ragDetails.chunks_used?.map((chunk, index) => ({
    key: index,
    ...chunk,
  })) || [];

  return (
    <Modal
      title={
        <Space>
          <SearchOutlined style={{ color: '#1890ff' }} />
          <span>Chi tiết RAG (Retrieval-Augmented Generation)</span>
        </Space>
      }
      open={visible}
      onCancel={onClose}
      footer={null}
      width={1000}
      style={{ top: 20 }}
    >
      <div style={{ padding: '16px 0' }}>
        {/* Query Section */}
        <div style={{ marginBottom: '24px' }}>
          <Title level={4}>
            <SearchOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
            Query được tìm kiếm
          </Title>
          <div style={{
            backgroundColor: '#f0f8ff',
            padding: '12px',
            borderRadius: '6px',
            border: '1px solid #d6e4ff',
            fontFamily: 'monospace',
            fontSize: '14px'
          }}>
            {ragDetails.query}
          </div>
        </div>

        <Divider />

        {/* RAG Status */}
        <div style={{ marginBottom: '24px' }}>
          <Title level={4}>
            <DatabaseOutlined style={{ marginRight: '8px', color: '#52c41a' }} />
            Trạng thái RAG
          </Title>
          <Space>
            <Tag color="green" size="large">
              Đã sử dụng RAG
            </Tag>
            <Text type="secondary">
              Tìm thấy {ragDetails.chunks_used?.length || 0} chunks liên quan
            </Text>
          </Space>
        </div>

        {/* Chunks Table */}
        {ragDetails.chunks_used && ragDetails.chunks_used.length > 0 ? (
          <>
            <Divider />
            <div style={{ marginBottom: '16px' }}>
              <Title level={4}>
                <FileTextOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
                Chunks được sử dụng ({ragDetails.chunks_used.length} chunks)
              </Title>
              <Text type="secondary">
                Các đoạn văn bản được tìm thấy và sử dụng để tạo câu trả lời
              </Text>
            </div>
            
            <Table
              columns={columns}
              dataSource={dataSource}
              pagination={false}
              size="small"
              scroll={{ y: 400 }}
              style={{ marginBottom: '16px' }}
            />
          </>
        ) : (
          <>
            <Divider />
            <div style={{ marginBottom: '16px' }}>
              <Title level={4}>
                <FileTextOutlined style={{ marginRight: '8px', color: '#faad14' }} />
                Không tìm thấy chunks phù hợp
              </Title>
              <Text type="secondary">
                Không có chunks nào có cosine similarity cao hơn threshold ({ragDetails.chunks_used?.length || 0} chunks)
              </Text>
            </div>
          </>
        )}

        {/* Context Used */}
        {ragDetails.context_used && (
          <>
            <Divider />
            <div>
              <Title level={4}>
                <FileTextOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
                Context được sử dụng
              </Title>
              <div style={{
                backgroundColor: '#f9f9f9',
                padding: '16px',
                borderRadius: '6px',
                border: '1px solid #d9d9d9',
                maxHeight: '300px',
                overflow: 'auto',
                fontFamily: 'monospace',
                fontSize: '13px',
                lineHeight: '1.5',
                whiteSpace: 'pre-wrap'
              }}>
                {ragDetails.context_used}
              </div>
            </div>
          </>
        )}

        {/* No Context Used */}
        {!ragDetails.context_used && (
          <>
            <Divider />
            <div style={{ textAlign: 'center', padding: '40px 0' }}>
              <FileTextOutlined style={{ fontSize: '48px', color: '#faad14', marginBottom: '16px' }} />
              <Title level={4} type="secondary">
                Không có context được sử dụng
              </Title>
              <Text type="secondary">
                Câu trả lời được tạo dựa trên kiến thức có sẵn của AI vì không tìm thấy chunks phù hợp
              </Text>
            </div>
          </>
        )}
      </div>
    </Modal>
  );
} 