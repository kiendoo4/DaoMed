import { Upload, Button, message } from "antd";
import { UploadOutlined, PaperClipOutlined } from "@ant-design/icons";
import Papa from "papaparse";
import { useState } from "react";

const CsvUpload = ({ onGetData }) => {
  const [fileName, setFileName] = useState(null);

  const props = {
    accept: ".csv",
    maxCount: 1,
    showUploadList: true,
    beforeUpload: (file) => {
      setFileName(file.name);

      const isCsv = file.type === "text/csv" || file.name.endsWith(".csv");
      if (!isCsv) {
        message.error("Chỉ chấp nhận file CSV.");
        return Upload.LIST_IGNORE;
      }

      const reader = new FileReader();
      reader.onload = () => {
        const csvText = reader.result;
        if (typeof csvText === "string") {
          Papa.parse(csvText, {
            header: true,
            skipEmptyLines: true,
            complete: function (results) {
              onGetData(
                results.data?.map((item) => ({
                  ...item,
                  question: String(item?.question)?.replace(/"/g, "").trim(),
                  expected_answer: String(item?.answer)
                    ?.replace(/"/g, "")
                    .trim(),
                }))
              );
              message.success("Đã đọc file CSV thành công.");
            },
            error: function (err) {
              message.error("Không thể parse file CSV.");
            },
          });
        }
      };

      reader.readAsText(file);
      return false;
    },
  };

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
      <Upload {...props} accept=".csv" showUploadList={false}>
        <Button icon={<UploadOutlined />}>Tải lên file CSV</Button>
      </Upload>
      {fileName && (
        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <PaperClipOutlined />
          <span>{fileName}</span>
        </div>
      )}
    </div>
  );
};

export default CsvUpload;
