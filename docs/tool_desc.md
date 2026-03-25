```
from pydantic import BaseModel, Field
class ToolModel(BaseModel):
        file_path:str = Field(..., description="파일의 절대 경로 (예: 'D:/Desktop_Pet/data/results/report.docx')")
        title:str = Field(..., description="문서 제목")
        content:str = Field(..., description="문서 본문 내용")
      
asd_tool = tool(
    func=create_word_doc,
    name="asd_tool",
    description="테스트용 도구입니다",
    args_schema=ToolModel
)
```
