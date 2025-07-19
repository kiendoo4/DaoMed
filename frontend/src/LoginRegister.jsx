import React, { useState } from "react";
import { Form, Input, Button, Tabs, message, Typography, Alert } from "antd";
import { authAPI } from "./api";

const { TabPane } = Tabs;
const { Title } = Typography;

export default function LoginRegister({ onLoginSuccess }) {
  const [tab, setTab] = useState("login");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [formLogin] = Form.useForm();
  const [formRegister] = Form.useForm();

  // Reset form khi chuyển tab
  const handleTabChange = (key) => {
    setTab(key);
    setError("");
    if (key === "login") formLogin.resetFields();
    if (key === "register") formRegister.resetFields();
  };

  const handleLogin = async (values) => {
    setLoading(true);
    setError("");
    try {
      const response = await authAPI.login(values);
      message.success("Đăng nhập thành công!");
      onLoginSuccess(values.username);
    } catch (e) {
      setError(
        e.response?.data?.error || "Đăng nhập thất bại. Vui lòng kiểm tra lại tài khoản/mật khẩu."
      );
    }
    setLoading(false);
  };

  const handleRegister = async (values) => {
    setLoading(true);
    setError("");
    try {
      const response = await authAPI.register(values);
      message.success("Đăng ký thành công! Hãy đăng nhập.");
      setTab("login");
      formRegister.resetFields();
    } catch (e) {
      setError(
        e.response?.data?.error || "Đăng ký thất bại. Vui lòng thử lại."
      );
    }
    setLoading(false);
  };

  return (
    <div style={{ maxWidth: 400, margin: "80px auto", background: "#fff", padding: 32, borderRadius: 8, boxShadow: "0 2px 8px #eee" }}>
      <Title level={2} style={{ textAlign: "center", marginBottom: 12 }}>Final Project: DaoMed</Title>
      <div style={{ textAlign: "center", marginBottom: 12 }}>kiendoo4, thuynguyen-99 and sirimiri13</div>
      <Tabs
        activeKey={tab}
        onChange={handleTabChange}
        centered
        destroyInactiveTabPane={true}
      >
        <TabPane tab="Đăng nhập" key="login">
          <Form
            form={formLogin}
            layout="vertical"
            onFinish={handleLogin}
            autoComplete="off"
          >
            <Form.Item
              name="username"
              label="Tên đăng nhập"
              rules={[{ required: true, message: "Nhập username" }]}
            >
              <Input autoFocus={tab === "login"} disabled={loading} />
            </Form.Item>
            <Form.Item
              name="password"
              label="Mật khẩu"
              rules={[{ required: true, message: "Nhập mật khẩu" }]}
            >
              <Input.Password disabled={loading} />
            </Form.Item>
            {error && <Alert type="error" message={error} showIcon style={{ marginBottom: 16 }} />}
            <Form.Item>
              <Button type="primary" htmlType="submit" block loading={loading}>
                Đăng nhập
              </Button>
            </Form.Item>
          </Form>
        </TabPane>
        <TabPane tab="Đăng ký" key="register">
          <Form
            form={formRegister}
            layout="vertical"
            onFinish={handleRegister}
            autoComplete="off"
          >
            <Form.Item
              name="username"
              label="Tên đăng ký"
              rules={[{ required: true, message: "Nhập username đăng ký" }]}
            >
              <Input autoFocus={tab === "register"} disabled={loading} />
            </Form.Item>
            <Form.Item
              name="password"
              label="Mật khẩu"
              rules={[{ required: true, message: "Nhập mật khẩu" }]}
            >
              <Input.Password disabled={loading} />
            </Form.Item>
            {error && <Alert type="error" message={error} showIcon style={{ marginBottom: 16 }} />}
            <Form.Item>
              <Button type="primary" htmlType="submit" block loading={loading}>
                Đăng ký
              </Button>
            </Form.Item>
          </Form>
        </TabPane>
      </Tabs>
    </div>
  );
} 