import { Typography, Input, Button, Form, Skeleton, Tabs, Table } from "antd";
import { useState } from "react";
import { evaluationAPI } from "../../api";
import CsvUpload from "./CsvUpload";
import ScoreTable from "./ScoreTable";

const { Title } = Typography;
const { TextArea } = Input;
const { TabPane } = Tabs;

const EvaluationPage = () => {
  const [singleData, setSingleData] = useState({});
  const [bulkData, setBulkData] = useState([]);
  const [rows, setRows] = useState([]);
  const [tab, setTab] = useState("manual");

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState([]);

  const handleEvaluate = async () => {
    const data = tab === "manual" ? [singleData] : bulkData;

    setLoading(true);
    await evaluationAPI
      .evaluate(data)
      .then((result) => {
        setResult(result.data);
        console.log("Evaluation result:", result.data);
      })
      .catch((err) => {
        console.error("Error during evaluation:", err);
      })
      .finally(() => setLoading(false));
  };

  const columns = [
    {
      title: "Câu hỏi",
      dataIndex: "question",
      key: "question",
    },
    {
      title: "Câu trả lời mong muốn",
      dataIndex: "expected_answer",
      key: "expected_answer",
    },
  ];

  const isValidInput = () => {
    if (tab === "manual") {
      return singleData.question && singleData.expected_answer;
    }
    return bulkData?.length > 0;
  };

  return (
    <div className="evaluation-placeholder">
      <Title
        level={2}
        style={{ color: "black", marginBottom: 16, textAlign: "center" }}
      >
        RAG Evaluation
      </Title>

      <Tabs activeKey={tab} onChange={setTab}>
        <TabPane tab="Nhập thủ công" key="manual">
          <Form layout="vertical" style={{ width: "100%" }}>
            <div style={{ display: "flex", gap: 16, width: "100%" }}>
              <Form.Item label="Câu hỏi" style={{ flex: 1, marginBottom: 0 }}>
                <TextArea
                  autoSize={{ minRows: 2, maxRows: 6 }}
                  value={singleData.question}
                  onChange={(e) =>
                    setSingleData((prev) => ({
                      ...prev,
                      question: e.target.value,
                    }))
                  }
                />
              </Form.Item>
              <Form.Item
                label="Câu trả lời mong muốn"
                style={{ flex: 1, marginBottom: 0 }}
              >
                <TextArea
                  autoSize={{ minRows: 2, maxRows: 6 }}
                  value={singleData.expected_answer}
                  onChange={(e) =>
                    setSingleData((prev) => ({
                      ...prev,
                      expected_answer: e.target.value,
                    }))
                  }
                />
              </Form.Item>
            </div>
          </Form>
        </TabPane>

        <TabPane tab="Upload CSV" key="upload">
          <CsvUpload
            onGetData={(data) => {
              setRows(data);
            }}
          />
          {rows?.length > 0 && (
            <>
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                }}
              >
                <Typography.Text type="secondary" style={{ marginTop: 8 }}>
                  Đã tải lên {rows.length} câu hỏi từ file CSV.
                </Typography.Text>
                <Typography.Text type="secondary" style={{ marginTop: 8 }}>
                  Bạn có thể chọn nhiều câu hỏi để đánh giá cùng lúc.
                </Typography.Text>
                {bulkData?.length > 0 && (
                  <Typography.Text type="secondary" style={{ marginTop: 8 }}>
                    Số lượng câu hỏi đã chọn: <b>{bulkData.length}</b>
                  </Typography.Text>
                )}
              </div>

              <Table
                rowKey={(row) => row.question + row.expected_answer}
                columns={columns}
                dataSource={rows}
                style={{ marginTop: 16 }}
                pagination={{ pageSize: 5 }}
                rowSelection={{
                  selectedRowKeys: bulkData.map(
                    (row) => row.question + row.expected_answer
                  ),
                  onChange: (_, selected) => setBulkData(selected),
                  selections: true,
                }}
                onRow={(record) => ({
                  onClick: () => {
                    const rowKey = record.question + record.expected_answer;
                    const isSelected = bulkData.some(
                      (row) => row.question + row.expected_answer === rowKey
                    );
                    const newSelected = isSelected
                      ? bulkData.filter(
                          (row) => row.question + row.expected_answer !== rowKey
                        )
                      : [...bulkData, record];
                    setBulkData(newSelected);
                  },
                })}
              />
            </>
          )}
        </TabPane>
      </Tabs>
      <div style={{ display: "flex", justifyContent: "center" }}>
        <Button
          type="primary"
          size="large"
          onClick={handleEvaluate}
          loading={loading}
          disabled={!isValidInput()}
          style={{ margin: 16, textTransform: "uppercase" }}
        >
          Đánh giá
        </Button>
      </div>

      {loading ? (
        <>
          <Skeleton.Node active size="large" style={{ width: "100%" }} />
          <Skeleton.Node active size="large" style={{ width: "100%" }} />
        </>
      ) : (
        result?.length > 0 && <ScoreTable data={result} />
      )}
    </div>
  );
};

export default EvaluationPage;
