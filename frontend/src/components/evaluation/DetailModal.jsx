import { Modal, Descriptions, Typography, Card, Space, Progress } from "antd";

const metricLabelMap = {
  answer_correctness: "Độ chính xác",
  context_recall: "Độ hồi tưởng",
  faithfulness: "Trung thực",
  semantic_similarity: "Tương đồng ngữ nghĩa",
};

const ScoreProgress = ({ score }) => {
  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      {Object.entries(score).map(([metric, value]) => (
        <div key={metric}>
          <Typography.Text strong>{metricLabelMap[metric]}</Typography.Text>
          <Progress percent={Math.round(value * 100)} strokeColor="#1890ff" />
        </div>
      ))}
    </Space>
  );
};

const DetailModal = ({ open, onClose, record }) => {
  if (!record) return null;

  return (
    <Modal
      title={
        <Typography.Title
          level={5}
          style={{ textTransform: "uppercase", textAlign: "center", margin: 0 }}
        >
          Chi tiết đánh giá
        </Typography.Title>
      }
      open={open}
      onCancel={onClose}
      width={700}
      footer={null}
      centered
    >
      <div
        style={{
          maxHeight: "80vh",
          overflowY: "auto",
          padding: 16,
          gap: 16,
          display: "flex",
          flexDirection: "column",
        }}
      >
        <Card>
          <ScoreProgress score={record.score} />
        </Card>
        <Descriptions column={1} size="small" bordered>
          <Descriptions.Item label="Câu hỏi">
            {record.question}
          </Descriptions.Item>
          <Descriptions.Item label="Câu trả lời mong muốn">
            {record.expected_answer}
          </Descriptions.Item>
          <Descriptions.Item label="Câu trả lời mô hình">
            {record.answer}
          </Descriptions.Item>
        </Descriptions>
      </div>
    </Modal>
  );
};

export default DetailModal;
