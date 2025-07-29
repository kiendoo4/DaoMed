import React, { useState } from "react";
import {
  Card,
  Row,
  Col,
  Button,
  Typography,
  Layout,
  Modal,
  Input,
  Select,
  Form,
  message,
  Slider,
} from "antd";
import {
  DatabaseOutlined,
  MessageOutlined,
  ExperimentOutlined,
  LogoutOutlined,
} from "@ant-design/icons";
import KnowledgeBaseSelector from "./components/KnowledgeBaseSelector";
import DialogList from "./components/DialogList";
import ChatWindow from "./components/ChatWindow";
import api from "./api";
import EvaluationPage from "./components/evaluation/EvaluationPage";

const { Header, Content } = Layout;
const { Title, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;

export default function MainInterface({ user, onLogout }) {
  const [currentView, setCurrentView] = useState("home"); // home, kb, chat, evaluation
  const [selectedDialogId, setSelectedDialogId] = useState(null);
  const [configModalVisible, setConfigModalVisible] = useState(false);
  const [configForm] = Form.useForm();
  const [configLoading, setConfigLoading] = useState(false);
  const [dialogListReloadKey, setDialogListReloadKey] = useState(0);

  const handleLogout = () => {
    onLogout();
  };

  const handleDialogSelect = (dialogId) => {
    setSelectedDialogId(dialogId);
  };

  // Callback khi gửi message thành công
  const handleMessageSent = () => {
    setDialogListReloadKey((k) => k + 1);
  };

  const handleConfigSubmit = async (values) => {
    if (!selectedDialogId) {
      message.error("No dialog selected");
      return;
    }

    try {
      setConfigLoading(true);

      const configData = {
        system_prompt: values.system_prompt,
        model_config: {
          model: values.model,
          temperature: parseFloat(values.temperature),
          max_tokens: parseInt(values.max_tokens),
        },
        max_chunks: parseInt(values.max_chunks),
        cosine_threshold: parseFloat(values.cosine_threshold),
      };

      await api.put(`/api/dialog/${selectedDialogId}/config`, configData);

      message.success("Dialog configuration updated successfully!");
      setConfigModalVisible(false);
    } catch (err) {
      console.error("Error updating config:", err);
      message.error(
        `Failed to update configuration: ${
          err.response?.data?.error || err.message
        }`
      );
    } finally {
      setConfigLoading(false);
    }
  };

  const showConfigModal = async () => {
    if (!selectedDialogId) {
      message.error("Please select a dialog first");
      return;
    }

    try {
      // Load current dialog config
      const response = await api.get(`/api/dialog/${selectedDialogId}`);
      const dialog = response.data;

      // Parse model config if it's a string
      let modelConfig = dialog.model_config;
      if (typeof modelConfig === "string") {
        try {
          modelConfig = JSON.parse(modelConfig);
        } catch (e) {
          console.error("Error parsing model config:", e);
          modelConfig = {
            model: "gemini-2.0-flash",
            temperature: 0.7,
            max_tokens: 1000,
          };
        }
      }

      configForm.setFieldsValue({
        system_prompt:
          dialog.system_prompt ||
          `You are a knowledgeable and helpful chatbot specializing in Traditional Eastern Medicine.
You answer user questions by retrieving and reasoning over information from the following six classical medical texts:

Shennong Bencao Jing (Thần Nông Bản Thảo)
Shanghan Lun (Thương Hàn Luận)
Nanjing (Nan Kinh)
Huangdi Neijing – Lingshu (Hoàng Đế Nội Kinh - Linh Khu)
Jingui Yaolue (Kim Quỹ Yếu Lược)
Qianjin Yaofang (Thiên Kim Yếu Phương)

Language Handling Rules:
If the user asks a question in Classical Chinese (chữ Hán), you must respond in Classical Chinese.
If the user uses Vietnamese, Modern Chinese, or English, respond in that language accordingly.
Always adapt your language based on the user's current usage.

Your Role:
Provide accurate, faithful answers based only on the content from the six books listed above.
Quote, summarize, or explain relevant passages as needed, but never fabricate information.
If a question cannot be sufficiently answered using the available knowledge base, respond politely and gently, acknowledging the limitation and expressing your intent to help as much as possible.`,
        model: modelConfig.model || "gemini-2.0-flash",
        temperature: modelConfig.temperature || 0.1,
        max_tokens: modelConfig.max_tokens || 1000,
        max_chunks: dialog.max_chunks || 8,
        cosine_threshold: dialog.cosine_threshold || 0.5,
      });

      setConfigModalVisible(true);
    } catch (err) {
      console.error("Error loading dialog config:", err);
      message.error("Failed to load dialog configuration");

      // Fallback to default values
      configForm.setFieldsValue({
        system_prompt: `You are a knowledgeable and helpful chatbot specializing in Traditional Eastern Medicine.
You answer user questions by retrieving and reasoning over information from the following six classical medical texts:

Shennong Bencao Jing (Thần Nông Bản Thảo)
Shanghan Lun (Thương Hàn Luận)
Nanjing (Nan Kinh)
Huangdi Neijing – Lingshu (Hoàng Đế Nội Kinh - Linh Khu)
Jingui Yaolue (Kim Quỹ Yếu Lược)
Qianjin Yaofang (Thiên Kim Yếu Phương)

Language Handling Rules:
If the user asks a question in Classical Chinese (chữ Hán), you must respond in Classical Chinese.
If the user uses Vietnamese, Modern Chinese, or English, respond in that language accordingly.
Always adapt your language based on the user's current usage.

Your Role:
Provide accurate, faithful answers based only on the content from the six books listed above.
Quote, summarize, or explain relevant passages as needed, but never fabricate information.
If a question cannot be sufficiently answered using the available knowledge base, respond politely and gently, acknowledging the limitation and expressing your intent to help as much as possible.`,
        model: "gemini-2.0-flash",
        temperature: 0.1,
        max_tokens: 1000,
        max_chunks: 8,
        cosine_threshold: 0.5,
      });
      setConfigModalVisible(true);
    }
  };

  const renderHomeView = () => (
    <div style={{ padding: "24px" }}>
      <Title level={2} style={{ textAlign: "center", marginBottom: "40px" }}>
        Chatbot dành cho ngữ liệu về Y học cổ truyền phương Đông!
      </Title>

      <Row gutter={[24, 24]} justify="center">
        <Col xs={24} sm={12} md={8}>
          <Card
            className="main-interface-card"
            hoverable
            style={{ height: "200px", textAlign: "center" }}
            onClick={() => setCurrentView("kb")}
          >
            <DatabaseOutlined
              style={{
                fontSize: "48px",
                color: "#1890ff",
                marginBottom: "16px",
              }}
            />
            <Title level={4}>Quản lý Knowledge Base</Title>
            <Text type="secondary">
              Upload và quản lý các file dữ liệu y học cổ truyền
            </Text>
          </Card>
        </Col>

        <Col xs={24} sm={12} md={8}>
          <Card
            className="main-interface-card"
            hoverable
            style={{ height: "200px", textAlign: "center" }}
            onClick={() => setCurrentView("chat")}
          >
            <MessageOutlined
              style={{
                fontSize: "48px",
                color: "#52c41a",
                marginBottom: "16px",
              }}
            />
            <Title level={4}>Chat & Dialogs</Title>
            <Text type="secondary">Quản lý dialogs và chat với AI</Text>
          </Card>
        </Col>

        <Col xs={24} sm={12} md={8}>
          <Card
            className="main-interface-card"
            hoverable
            style={{ height: "200px", textAlign: "center" }}
            onClick={() => setCurrentView("evaluation")}
          >
            <ExperimentOutlined
              style={{
                fontSize: "48px",
                color: "#fa8c16",
                marginBottom: "16px",
              }}
            />
            <Title level={4}>RAG Evaluation</Title>
            <Text type="secondary">
              Đánh giá hiệu suất của phương pháp RAG cho chatbot
            </Text>
          </Card>
        </Col>
      </Row>
    </div>
  );

  const renderKnowledgeBaseView = () => (
    <div>
      <Title level={3} style={{ textAlign: "center" }}>
        Quản lý Knowledge Base
      </Title>
      <KnowledgeBaseSelector />
    </div>
  );

  const renderChatView = () => (
    <div
      style={{
        height: "calc(108vh - 120px)",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Title level={3} style={{ marginTop: 0 }}>
        Chat & Dialogs
      </Title>

      <Row
        gutter={24}
        style={{
          flex: 1,
          minHeight: 0, // Important for flex child
          overflow: "hidden",
        }}
      >
        {/* Dialog List - Cột nhỏ */}
        <Col xs={24} md={6} lg={5} style={{ height: "100%" }}>
          <Card
            title="Dialogs"
            style={{
              height: "100%",
              display: "flex",
              flexDirection: "column",
            }}
            bodyStyle={{
              padding: "12px",
              flex: 1,
              overflow: "hidden",
              display: "flex",
              flexDirection: "column",
            }}
          >
            <DialogList
              onSelect={handleDialogSelect}
              selectedId={selectedDialogId}
              reloadKey={dialogListReloadKey}
            />
          </Card>
        </Col>

        {/* Chat Window - Cột lớn */}
        <Col xs={24} md={18} lg={19} style={{ height: "100%" }}>
          <Card
            style={{
              height: "100%",
              display: "flex",
              flexDirection: "column",
              padding: 0,
            }}
            bodyStyle={{
              flex: 1,
              display: "flex",
              flexDirection: "column",
              padding: 0,
              overflow: "hidden", // Đảm bảo Card body không scroll
            }}
          >
            <ChatWindow
              dialogId={selectedDialogId}
              onMessageSent={handleMessageSent}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Header
        style={{
          background: "#fff",
          padding: "0 24px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
        }}
      >
        <Title
          level={3}
          style={{ margin: 0, color: "#1890ff", cursor: "pointer" }}
          onClick={() => setCurrentView("home")}
        >
          DaoMed
        </Title>
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <Text>Xin chào, {user}</Text>
          <Button
            type="primary"
            danger
            icon={<LogoutOutlined />}
            onClick={handleLogout}
          >
            Đăng xuất
          </Button>
        </div>
      </Header>

      <Content style={{ padding: "24px" }}>
        {currentView !== "home" && (
          <div style={{ marginBottom: "24px" }}>
            <Button onClick={() => setCurrentView("home")}>
              ← Về trang chủ
            </Button>
          </div>
        )}
        {currentView === "home" && renderHomeView()}
        {currentView === "kb" && renderKnowledgeBaseView()}
        {currentView === "chat" && renderChatView()}
        {currentView === "evaluation" && <EvaluationPage />}
      </Content>

      {/* Config Modal */}
      <Modal
        title="Dialog Configuration"
        open={configModalVisible}
        onCancel={() => setConfigModalVisible(false)}
        footer={null}
        width={800}
      >
        <Form form={configForm} layout="vertical" onFinish={handleConfigSubmit}>
          <Form.Item
            label="System Prompt"
            name="system_prompt"
            rules={[{ required: true, message: "Please enter system prompt" }]}
          >
            <TextArea
              rows={12}
              placeholder="Enter system prompt for the AI..."
            />
          </Form.Item>

          <Form.Item
            label="Model"
            name="model"
            rules={[{ required: true, message: "Please select model" }]}
          >
            <Select>
              <Option value="gemini-2.0-flash">Gemini 2.0 Flash</Option>
              <Option value="gemini-2.0-flash-thinking-mode">
                Gemini 2.0 Flash (Thinking Mode)
              </Option>
              <Option value="gemini-2.0-flash-lite">
                Gemini 2.0 Flash Lite
              </Option>
              <Option value="gemini-2.5-flash">Gemini 2.5 Flash</Option>
              <Option value="gemini-2.5-flash-lite">
                Gemini 2.5 Flash Lite
              </Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="Temperature (0.0 - 1.0)"
            name="temperature"
            rules={[{ required: true, message: "Please select temperature" }]}
          >
            <Slider
              min={0}
              max={1}
              step={0.1}
              marks={{
                0: "0",
                0.5: "0.5",
                1: "1",
              }}
              tooltip={{
                formatter: (value) => `${value}`,
              }}
            />
          </Form.Item>

          <Form.Item
            label="Max Tokens"
            name="max_tokens"
            rules={[
              { required: true, message: "Please enter max tokens" },
              {
                type: "number",
                min: 1,
                max: 8192,
                message: "Max tokens must be between 1 and 8192",
              },
            ]}
          >
            <Input type="number" min={1} max={8192} placeholder="1000" />
          </Form.Item>

          <Form.Item
            label="Max Chunks (1-30)"
            name="max_chunks"
            rules={[{ required: true, message: "Please select max chunks" }]}
          >
            <Slider
              min={1}
              max={30}
              step={1}
              marks={{
                1: "1",
                10: "10",
                20: "20",
                30: "30",
              }}
              tooltip={{
                formatter: (value) => `${value}`,
              }}
            />
          </Form.Item>

          <Form.Item
            label="Cosine Threshold (0.0-1.0)"
            name="cosine_threshold"
            rules={[
              { required: true, message: "Please select cosine threshold" },
            ]}
          >
            <Slider
              min={0}
              max={1}
              step={0.1}
              marks={{
                0: "0",
                0.5: "0.5",
                1: "1",
              }}
              tooltip={{
                formatter: (value) => `${value}`,
              }}
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={configLoading}
              style={{ marginRight: 8 }}
            >
              Save Configuration
            </Button>
            <Button onClick={() => setConfigModalVisible(false)}>Cancel</Button>
          </Form.Item>
        </Form>
      </Modal>
    </Layout>
  );
}
