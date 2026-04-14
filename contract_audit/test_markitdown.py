from markitdown import MarkItDown

md = MarkItDown()
result = md.convert("d:/AICodingProject/htsh-ai/contract_audit/uploads/cffd9a60f8e444a29417ccdcd2fe0a5d.pdf")

with open("d:/AICodingProject/htsh-ai/markitdown_output.md", "w", encoding="utf-8") as f:
    f.write(result.text_content)

print("转换完成，输出到 markitdown_output.md")