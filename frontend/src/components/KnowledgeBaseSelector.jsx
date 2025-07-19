import { useState, useEffect } from 'react';
import { 
  Upload, 
  Button, 
  Card, 
  Row, 
  Col, 
  Typography, 
  Space, 
  Progress,
  Form,
  Input,
  Divider,
  message,
  Alert,
  Table,
  Tag,
  Modal,
  Tooltip,
  Popconfirm,
  Pagination
} from 'antd';
import { 
  UploadOutlined, 
  FileExcelOutlined, 
  FileTextOutlined,
  CheckCircleOutlined,
  DeleteOutlined,
  EyeOutlined,
  DatabaseOutlined
} from '@ant-design/icons';
import api, { kbAPI } from '../api';

const { Text } = Typography;
const { Dragger } = Upload;

export default function KnowledgeBaseSelector() {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStage, setUploadStage] = useState('');
  const [currentFile, setCurrentFile] = useState(null);
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [chunks, setChunks] = useState([]);
  const [loadingChunks, setLoadingChunks] = useState(false);
  const [selectedChunk, setSelectedChunk] = useState(null);
  const [chunkVector, setChunkVector] = useState(null);
  const [loadingVector, setLoadingVector] = useState(false);
  const [isVectorModalVisible, setIsVectorModalVisible] = useState(false);
  // Pagination state for chunks
  const [chunksPage, setChunksPage] = useState(1);
  const [chunksPageSize, setChunksPageSize] = useState(100);
  const [chunksPagination, setChunksPagination] = useState(null);
  const [totalChunks, setTotalChunks] = useState(0);
  // Removed chunking settings since we use row-based chunking

  useEffect(() => {
    fetchFiles();
  }, []);

  const fetchFiles = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/kb/list');
      setFiles(response.data.files || []);
    } catch (err) {
      console.error('Error fetching files:', err);
      message.error('Không thể tải danh sách file');
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (file) => {
    const isExcel = file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' || 
                   file.type === 'application/vnd.ms-excel';
    const isCsv = file.type === 'text/csv' || file.name.endsWith('.csv');
    
    if (!isExcel && !isCsv) {
      message.error('Chỉ hỗ trợ file Excel (.xlsx, .xls) hoặc CSV (.csv)!');
      return false;
    }

    const isLt10M = file.size / 1024 / 1024 < 10;
    if (!isLt10M) {
      message.error('File phải nhỏ hơn 10MB!');
      return false;
    }

    setUploading(true);
    setUploadProgress(0);
    setUploadStage('Đang upload file...');
    setCurrentFile(file);

    const formData = new FormData();
    formData.append('file', file);

    try {
      await kbAPI.upload(formData, (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        setUploadProgress(percentCompleted);
        
        // Update stage based on progress
        if (percentCompleted < 50) {
          setUploadStage('Đang upload file...');
        } else if (percentCompleted < 80) {
          setUploadStage('Đang xử lý file...');
        } else if (percentCompleted < 95) {
          setUploadStage('Đang tạo chunks...');
        } else {
          setUploadStage('Đang lưu vào vector database...');
        }
      });

      message.success('Upload và xử lý thành công!');
      setUploadProgress(100);
      setUploadStage('Hoàn thành!');
      
      // Refresh danh sách file
      fetchFiles();
      
      return false;
    } catch (err) {
      console.error('Upload error:', err);
      message.error(`Upload thất bại: ${err.response?.data?.error || err.message}`);
      setUploadProgress(0);
      setUploadStage('');
      setCurrentFile(null);
      return false;
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (fileId) => {
    try {
      await api.delete(`/api/kb/${fileId}`);
      message.success('Xóa file thành công!');
      fetchFiles();
    } catch (err) {
      message.error(`Xóa thất bại: ${err.response?.data?.error || err.message}`);
    }
  };

  const handleViewChunks = async (file, page = 1) => {
    setSelectedFile(file);
    setIsModalVisible(true);
    setLoadingChunks(true);
    setChunksPage(page);
    
    try {
      const response = await api.get(`/api/kb/${file.id}/chunks?page=${page}&page_size=${chunksPageSize}`);
      setChunks(response.data.chunks || []);
      setChunksPagination(response.data.pagination);
      setTotalChunks(response.data.total_chunks || 0);
    } catch (err) {
      console.error('Error fetching chunks:', err);
      message.error('Không thể tải chunks');
      setChunks([]);
      setChunksPagination(null);
      setTotalChunks(0);
    } finally {
      setLoadingChunks(false);
    }
  };

  const handleViewVector = async (chunk) => {
    setSelectedChunk(chunk);
    setIsVectorModalVisible(true);
    setLoadingVector(true);
    setChunkVector(null);
    
    try {
      const response = await api.get(`/api/kb/${selectedFile.id}/chunks/${chunk.id}/vector`);
      setChunkVector(response.data);
    } catch (err) {
      console.error('Error fetching vector:', err);
      message.error('Không thể tải vector');
    } finally {
      setLoadingVector(false);
    }
  };

  const columns = [
    {
      title: 'Tên file',
      dataIndex: 'filename',
      key: 'filename',
      render: (text, record) => (
        <Space>
          {record.filename.endsWith('.csv') ? 
            <FileTextOutlined style={{ color: '#52c41a' }} /> : 
            <FileExcelOutlined style={{ color: '#1890ff' }} />
          }
          <Text strong>{text}</Text>
        </Space>
      ),
    },
    {
      title: 'Kích thước',
      dataIndex: 'file_size',
      key: 'file_size',
      render: (size) => {
        if (!size || size === 0) return 'N/A';
        const sizeInMB = (size / 1024 / 1024).toFixed(2);
        return `${sizeInMB} MB`;
      },
    },
    {
      title: 'Số chunks',
      dataIndex: 'num_chunks',
      key: 'num_chunks',
      render: (chunks) => (
        <Tag color={chunks > 0 ? 'green' : 'red'}>
          {chunks || 0} chunks
        </Tag>
      ),
    },
    {
      title: 'Ngày upload',
      dataIndex: 'uploaded_at',
      key: 'uploaded_at',
      render: (date) => date ? new Date(date).toLocaleDateString('vi-VN') : 'N/A',
    },
    {
      title: 'Thao tác',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Tooltip title="Xem chunks">
            <Button 
              type="text" 
              icon={<EyeOutlined />} 
              onClick={() => handleViewChunks(record)}
            />
          </Tooltip>

          <Popconfirm
            title="Bạn có chắc muốn xóa file này?"
            onConfirm={() => handleDelete(record.id)}
            okText="Có"
            cancelText="Không"
          >
            <Tooltip title="Xóa">
              <Button 
                type="text" 
                danger 
                icon={<DeleteOutlined />} 
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      {/* Upload Section */}
      <Card 
        title={
          <Space>
            <UploadOutlined />
            <span>Upload Knowledge Base</span>
          </Space>
        }
        style={{ marginBottom: '24px' }}
      >
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <Dragger
              name="file"
              multiple={false}
              beforeUpload={handleUpload}
              accept=".xlsx,.xls,.csv"
              disabled={uploading}
              showUploadList={false}
            >
              <p className="ant-upload-drag-icon">
                <UploadOutlined />
              </p>
              <p className="ant-upload-text">Click hoặc kéo file vào đây để upload</p>
              <p className="ant-upload-hint">
                Hỗ trợ file Excel (.xlsx, .xls) và CSV (.csv). Tối đa 10MB.
              </p>
            </Dragger>
          </Col>
          
          {uploading && (
            <Col span={24}>
              <Progress 
                percent={uploadProgress} 
                status="active"
                strokeColor={{
                  '0%': '#108ee9',
                  '100%': '#87d068',
                }}
                format={(percent) => `${percent}%`}
              />
              <Text type="secondary" style={{ marginTop: '8px', display: 'block' }}>
                {uploadStage} - {currentFile?.name}
              </Text>
            </Col>
          )}

          {uploadProgress === 100 && (
            <Col span={24}>
              <Alert
                message="Upload thành công!"
                description="File đã được xử lý và sẵn sàng sử dụng cho chat."
                type="success"
                showIcon
                icon={<CheckCircleOutlined />}
              />
            </Col>
          )}
        </Row>

        {/* Chunking Info */}
        <Divider orientation="left">Thông tin Chunking</Divider>
        <Alert
          message="Row-based Chunking"
          description="Mỗi row trong bảng sẽ tự động trở thành một chunk riêng biệt"
          type="info"
          showIcon
        />
      </Card>

      {/* Files List */}
      <Card 
        title={
          <Space>
            <DatabaseOutlined />
            <span>Files đã upload ({files.length})</span>
          </Space>
        }
      >
        {files.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <FileExcelOutlined style={{ fontSize: '48px', color: '#d9d9d9', marginBottom: '16px' }} />
            <Text type="secondary">Chưa có file nào. Hãy upload file đầu tiên!</Text>
          </div>
        ) : (
          <Table
            columns={columns}
            dataSource={files}
            rowKey="id"
            pagination={false}
            size="middle"
            loading={loading}
          />
        )}
      </Card>

      {/* Chunks Modal */}
      <Modal
        title={`Chunks của file: ${selectedFile?.filename}`}
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setIsModalVisible(false)}>
            Đóng
          </Button>
        ]}
        width={1000}
        style={{ top: 20 }}
      >
        {selectedFile && (
          <div>
            <Row gutter={[16, 16]} style={{ marginBottom: '16px' }}>
              <Col span={8}>
                <Text strong>Tên file:</Text>
                <br />
                <Text>{selectedFile.filename}</Text>
              </Col>
              <Col span={8}>
                <Text strong>Tổng số chunks:</Text>
                <br />
                <Text>{totalChunks || selectedFile.num_chunks || 0}</Text>
              </Col>
              <Col span={8}>
                <Text strong>Ngày upload:</Text>
                <br />
                <Text>{selectedFile.uploaded_at ? new Date(selectedFile.uploaded_at).toLocaleString('vi-VN') : 'N/A'}</Text>
              </Col>
            </Row>
            
            <Divider orientation="left">Danh sách Chunks</Divider>
            
            {loadingChunks ? (
              <div style={{ textAlign: 'center', padding: '40px' }}>
                <Text>Đang tải chunks...</Text>
              </div>
            ) : chunks.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px' }}>
                <Text type="secondary">Không tìm thấy chunks</Text>
              </div>
            ) : (
              <div>
                <div style={{ maxHeight: '500px', overflowY: 'auto' }}>
                  {chunks.map((chunk, index) => (
                    <div 
                      key={chunk.id} 
                      style={{ 
                        border: '1px solid #d9d9d9', 
                        margin: '8px 0', 
                        padding: '12px', 
                        borderRadius: '6px',
                        backgroundColor: '#fafafa'
                      }}
                    >
                      <div style={{ 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        alignItems: 'center',
                        marginBottom: '8px'
                      }}>
                        <div style={{ 
                          fontWeight: 'bold', 
                          color: '#1890ff',
                          fontSize: '14px'
                        }}>
                          Chunk #{chunk.id} (Row {chunk.row_index})
                        </div>
                        <Button 
                          type="text" 
                          size="small"
                          icon={<DatabaseOutlined />}
                          onClick={() => handleViewVector(chunk)}
                          title="Xem vector"
                        >
                          Vector
                        </Button>
                      </div>
                      <div style={{ 
                        fontFamily: 'monospace', 
                        fontSize: '13px', 
                        lineHeight: '1.5',
                        wordBreak: 'break-word',
                        backgroundColor: '#fff',
                        padding: '8px',
                        borderRadius: '4px',
                        border: '1px solid #f0f0f0'
                      }}>
                        {chunk.text}
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* Pagination Controls */}
                {chunksPagination && totalChunks > 0 && (
                  <div style={{ 
                    marginTop: '16px', 
                    textAlign: 'center',
                    borderTop: '1px solid #f0f0f0',
                    paddingTop: '16px'
                  }}>
                    <Pagination
                      current={chunksPagination.page}
                      total={totalChunks}
                      pageSize={chunksPagination.page_size}
                      showSizeChanger={false}
                      showQuickJumper
                      showTotal={(total, range) => 
                        `${range[0]}-${range[1]} của ${total} chunks`
                      }
                      onChange={(page) => handleViewChunks(selectedFile, page)}
                    />
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* Vector Modal */}
      <Modal
        title={`Vector của Chunk #${selectedChunk?.id}`}
        open={isVectorModalVisible}
        onCancel={() => setIsVectorModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setIsVectorModalVisible(false)}>
            Đóng
          </Button>
        ]}
        width={800}
        style={{ top: 20 }}
      >
        {selectedChunk && (
          <div>
            <Row gutter={[16, 16]} style={{ marginBottom: '16px' }}>
              <Col span={12}>
                <Text strong>Chunk ID:</Text>
                <br />
                <Text>{selectedChunk.id}</Text>
              </Col>
              <Col span={12}>
                <Text strong>Row Index:</Text>
                <br />
                <Text>{selectedChunk.row_index}</Text>
              </Col>
            </Row>
            
            <Divider orientation="left">Nội dung Chunk</Divider>
            <div style={{ 
              fontFamily: 'monospace', 
              fontSize: '13px', 
              lineHeight: '1.5',
              wordBreak: 'break-word',
              backgroundColor: '#f5f5f5',
              padding: '12px',
              borderRadius: '4px',
              border: '1px solid #d9d9d9',
              marginBottom: '16px'
            }}>
              {selectedChunk.text}
            </div>
            
            <Divider orientation="left">Vector Information</Divider>
            
            {loadingVector ? (
              <div style={{ textAlign: 'center', padding: '40px' }}>
                <Text>Đang tải vector...</Text>
              </div>
            ) : chunkVector ? (
              <div>
                <Row gutter={[16, 16]} style={{ marginBottom: '16px' }}>
                  <Col span={8}>
                    <Text strong>Vector Size:</Text>
                    <br />
                    <Text>{chunkVector.vector_size} dimensions</Text>
                  </Col>
                  <Col span={8}>
                    <Text strong>KB ID:</Text>
                    <br />
                    <Text>{chunkVector.kb_id}</Text>
                  </Col>
                  <Col span={8}>
                    <Text strong>Chunk ID:</Text>
                    <br />
                    <Text>{chunkVector.chunk_id}</Text>
                  </Col>
                </Row>
                
                <div style={{ marginBottom: '16px' }}>
                  <Text strong>Vector Preview (first 10 values):</Text>
                  <div style={{ 
                    fontFamily: 'monospace', 
                    fontSize: '12px', 
                    backgroundColor: '#f0f0f0',
                    padding: '8px',
                    borderRadius: '4px',
                    border: '1px solid #d9d9d9',
                    maxHeight: '100px',
                    overflowY: 'auto'
                  }}>
                    [{chunkVector.vector.slice(0, 10).map(v => v.toFixed(6)).join(', ')}...]
                  </div>
                </div>
                
                <div>
                  <Text strong>Full Vector:</Text>
                  <div style={{ 
                    fontFamily: 'monospace', 
                    fontSize: '11px', 
                    backgroundColor: '#f0f0f0',
                    padding: '8px',
                    borderRadius: '4px',
                    border: '1px solid #d9d9d9',
                    maxHeight: '200px',
                    overflowY: 'auto',
                    whiteSpace: 'pre-wrap'
                  }}>
                    {JSON.stringify(chunkVector.vector, null, 2)}
                  </div>
                </div>
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '40px' }}>
                <Text type="secondary">Không tìm thấy vector</Text>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
} 