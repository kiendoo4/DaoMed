import React, { useState } from "react";
import { Layout, Menu } from "antd";
import {
  MessageOutlined,
  DatabaseOutlined,
  LogoutOutlined,
} from "@ant-design/icons";
import ChatPage from "./ChatPage";
import KnowledgeBasePage from "./KnowledgeBasePage";

const { Header, Sider, Content } = Layout;

export default function MainLayout({ user, onLogout }) {
  const [selected, setSelected] = useState("chat");

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider width={220} style={{ background: "#fff" }}>
        <div
          style={{
            height: 64,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontWeight: "bold",
            fontSize: 22,
            borderBottom: "1px solid #eee",
            marginBottom: 8,
          }}
        >
          NLP FINAL PROJECT
        </div>
        <Menu
          mode="inline"
          selectedKeys={[selected]}
          onClick={(e) => setSelected(e.key)}
          style={{ borderRight: 0, fontSize: 16 }}
        >
          <Menu.Item key="chat" icon={<MessageOutlined />}>
            Chat
          </Menu.Item>
          <Menu.Item key="kb" icon={<DatabaseOutlined />}>
            Knowledge Base
          </Menu.Item>
          <Menu.Item
            key="logout"
            icon={<LogoutOutlined />}
            onClick={onLogout}
            style={{ marginTop: 32, color: "#d4380d" }}
          >
            Đăng xuất
          </Menu.Item>
        </Menu>
      </Sider>
      <Layout>
        <Header
          style={{
            background: "#fff",
            borderBottom: "1px solid #eee",
            fontSize: 18,
            fontWeight: 500,
            padding: "0 24px",
            display: "flex",
            alignItems: "center",
            height: 64,
          }}
        >
          Xin chào, {user}!
        </Header>
        <Content style={{ margin: 0, padding: 24, background: "#f5f5f5" }}>
          <div style={{ maxWidth: 900, margin: "0 auto" }}>
            {selected === "chat" && <ChatPage />}
            {selected === "kb" && <KnowledgeBasePage />}
          </div>
        </Content>
      </Layout>
    </Layout>
  );
}
