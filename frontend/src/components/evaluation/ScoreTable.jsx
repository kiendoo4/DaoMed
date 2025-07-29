import { Table, Button } from "antd";
import { useState } from "react";
import DetailModal from "./DetailModal";

const ScoreTable = ({ data }) => {
  const [selectedRow, setSelectedRow] = useState(null);
  const [open, setOpen] = useState(false);

  const showModal = (record) => {
    setSelectedRow(record);
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
    setSelectedRow(null);
  };

  const columns = [
    {
      title: "Câu hỏi",
      dataIndex: "question",
      key: "question",
      width: 250,
      ellipsis: true,
    },
    {
      title: "Câu trả lời mong muốn",
      dataIndex: "expected_answer",
      key: "expected_answer",
      width: 250,
      ellipsis: true,
    },
    {
      title: "Câu trả lời",
      dataIndex: "answer",
      key: "answer",
      width: 300,
      ellipsis: true,
    },
    {
      title: "Điểm số",
      children: [
        {
          title: "Độ chính xác",
          key: "correctness",
          render: (_, record) => record.score.answer_correctness?.toFixed(3),
        },
        {
          title: "Độ bao phủ ngữ cảnh",
          key: "recall",
          render: (_, record) => record.score.context_recall?.toFixed(3),
        },
        {
          title: "Độ trung thực",
          key: "faithfulness",
          render: (_, record) => record.score.faithfulness?.toFixed(3),
        },
        {
          title: "Độ tương đồng ngữ nghĩa",
          key: "similarity",
          render: (_, record) => record.score.semantic_similarity?.toFixed(3),
        },
      ],
    },
    {
      title: "Chi tiết",
      key: "detail",
      render: (_, record) => (
        <Button type="link" onClick={() => showModal(record)}>
          Xem chi tiết
        </Button>
      ),
    },
  ];

  return (
    <>
      <Table
        columns={columns}
        dataSource={data.map((item, idx) => ({ ...item, key: idx.toString() }))}
        pagination={{ pageSize: 5 }}
      />
      <DetailModal open={open} onClose={handleClose} record={selectedRow} />
    </>
  );
};

export default ScoreTable;
