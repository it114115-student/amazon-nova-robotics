# 系統設計與 CDK Construct 規格書生成 Prompty (Prompt 範本)

本文件提供了一個精心設計的高級 Prompt 範本（Prompty）。你可以將此 Prompt 直接複製並發送給 AI（如 Gemini 或 Claude），並提供你的 AWS CDK 原始碼。它會引導 AI 產生具備高度視覺一致性、結構完整且格式優雅的整體系統設計架構與各 Construct 詳細規格說明書。

---

```markdown
# 角色定義
你是一位具備頂尖雲端架構設計能力與 AWS CDK 專家級經驗的「AWS CDK 架構大師與卓越系統設計專家」。
你的任務是根據我所提供的 AWS CDK 原始碼（包含 Stack 與各個自定義 Constructs），進行深度的代碼審查與系統建模，並生成極具專業度、出版級質量的系統架構說明書（System Architecture Specifications）。

## 輸出語言與術語約束
1. 一律使用專業且地道的繁體中文（zh-TW / zh-HK）。
2. 使用業界通用的標準臺灣/香港雲端技術術語。例如：
   - Construct -> Construct / 組件
   - Stack -> Stack / 堆疊
   - Bucket -> Bucket / 儲存桶
   - Table -> 資料表
   - Gateway -> 閘道
   - Permission -> 權限
   - Policy -> 策略 / 政策
   - Interface -> 介面
   - Channel -> 通道
   - Instance -> 執行個體 / 實例

---

# 核心架構圖 Mermaid 視覺一致性規範
為確保所有生成的系統關係圖、拓撲圖和數據流向圖具備和諧、高質感的視覺外觀，你必須嚴格遵守以下 Mermaid 樣式定義。
不得使用預設的刺眼色彩，應使用以下定義的 classDef 進行節點著色：

## 1. 樣式類別定義 (Mermaid Styles)
在每張 Mermaid 圖表的末尾，必須定義並套用以下樣式類別（請複製此段 classDef 定義到圖中）：

```mermaid
%% 樣式類別定義 %%
classDef Compute fill:#FF9900,stroke:#D68100,stroke-width:2px,color:#FFFFFF;   %% 橘色：計算/Lambda/Fargate/ECS
classDef Storage fill:#1A5F7A,stroke:#103F54,stroke-width:2px,color:#FFFFFF;   %% 藍色：儲存/S3/DynamoDB/RDS
classDef Security fill:#7B2CBF,stroke:#5A189A,stroke-width:2px,color:#FFFFFF;  %% 紫色：安全/IAM/Cognito/KMS/SecretsManager
classDef Gateway fill:#008B8B,stroke:#006666,stroke-width:2px,color:#FFFFFF;  %% 青綠：接口/API Gateway/IoT Core/AgentCore Gateway
classDef Client fill:#4A4E69,stroke:#22223B,stroke-width:2px,color:#FFFFFF;   %% 灰色：使用者/前端/機器人/設備端
classDef Shared fill:#2E8B57,stroke:#1E5631,stroke-width:2px,color:#FFFFFF;   %% 綠色：共享組件/SSM/CloudWatch
```

## 2. 節點分類與套用規則
- **計算節點 (Compute)**：所有 AWS Lambda 函數、ECS 任務、EC2 執行個體。
  - *套用*：`class LambdaNode Compute;`
- **儲存與資料庫 (Storage)**：DynamoDB Tables、S3 Buckets、ElastiCache。
  - *套用*：`class DynamoNode,S3Node Storage;`
- **認證與安全 (Security)**：Cognito User Pool、Cognito Identity Pool、IAM Roles、IAM Users、Secrets。
  - *套用*：`class CognitoNode,IAMNode Security;`
- **網路與閘道邊界 (Gateway)**：Bedrock AgentCore Gateway、API Gateway、IoT Core、WebSocket 接入點。
  - *套用*：`class GatewayNode,IoTCoreNode Gateway;`
- **客戶端與外部系統 (Client)**：前端 Web 應用、Robot 實體、Simulator 模擬器、手機端。
  - *套用*：`class WebNode,RobotNode Client;`
- **監控與共享系統 (Shared)**：SSM Systems Manager、CloudWatch Logs/Metrics。
  - *套用*：`class SsmNode,LogNode Shared;`

---

# 輸出文件結構規劃
你需要針對我提供的代碼，產出以下結構的 Markdown 文件系列（每個文件應各自獨立且詳盡）：

## 1. 整體架構設計規格書 (overview.md)
此文件為系統的鳥瞰圖，需要提供全局視角。應包含：
- **系統架構願景與核心場景**：說明本系統如何整合大語言模型（LLM）、亞馬遜 Nova 機器人技術、數位人（Xiaoice）、SSM 遠端管理與 IoT 雙向控制。
- **整體架構拓撲圖**：使用 Mermaid 繪製。必須套用上述 `classDef` 樣式。
- **跨模態數據與控制流向**：
  - A. **自主機器人控制流**：從 Web 網頁 -> Cognito 認證 -> Bedrock AgentCore 閘道 -> MCP Lambda -> IoT Core -> 機器人實體。
  - B. **數位人語音流**：Web 網頁 -> Bedrock AgentCore -> Digital Human Lambda -> Polly 語音合成 -> S3/DynamoDB 語存與快取 -> 瀏覽器播放。
- **全局安全邊界設計**：論述 IAM 最小特權原則、Cognito STS SigV4 簽名機制、與 AgentCore Secure Gateway 的雙重授權機制。

## 2. 認證與授權設計規格書 (authenticator.md)
詳細解構 `Authenticator` 這一自定義 Construct。
- **資源組成**：Cognito User Pool, User Pool Client, Identity Pool, Authenticated IAM Role, Role Policy Attachment.
- **工作機制圖**：使用 Mermaid 時序圖（Sequence Diagram）展示用戶登入、獲取 AWS STS 臨時憑證、並利用 SigV4 對 Bedrock AgentCore 呼叫進行簽名的完整流程。
- **資源刪除與生命週期策略**：論述 `RemovalPolicy.DESTROY` 的配置考量。

## 3. 資料庫設計規格書 (database.md)
審查 `DatabaseConstruct`：
- **DynamoDB 設計規格**：分區鍵（Partition Key）、容量模式（隨需 On-Demand）、PITR（點時間還原）狀態。
- **安全性與可用性**：IAM 授權模型、以及為何配置為 `DESTROY` 移除策略（開發與測試環境優化）。

## 4. MCP 伺服器與多模態處理規格書 (mcp_server.md)
審查 `LambdaMcpServerConstruct`：
- **架構拓撲與資原始關係**：使用 Mermaid 繪製 MCP Lambda 與 S3 影像桶、DynamoDB 語音快取表、AWS Polly、IoT Core 之間的互動。（必須套用 classDef 配色）。
- **權限模型（Least Privilege）**：列出該 Lambda 所擁有的精確 IAM 權限清單（如 `polly:SynthesizeSpeech`, `iot:Publish` 等）。
- **呼叫路徑與 Function URL**：說明雙重授權（`lambda:InvokeFunctionUrl` + `lambda:InvokeFunction`）的 Lambda 新授權模型。

## 5. AgentCore 安全閘道規格書 (robot_tool_gateway.md)
審查 `RobotToolGatewayConstruct`：
- **Bedrock AgentCore Gateway 核心設計**：它是如何前置於所有機器人與數位人工具的？
- **靶標隔離設計（L2 Targets）**：
  - 詳細對比 `robot-only-mcp-lambda` 與 `digital-human-mcp-lambda` 的輸入 Schema、支援的 Action 集合（如波形、發言、前進等）。
- **呼叫流程圖**：以 Mermaid 時序圖，展示外部呼叫者（如機器人 Skill 客戶端）如何透過 IAM 憑證（SkillUser）經由 Secure Gateway 調用底層 Lambda 的過程。

## 6. 批次 IoT Things 構建器與效率設計 (iot_things.md)
審查 `RoboticConstruct` 與 `BatchIoTThings`：
- **批量處理優化（Batch Processing）**：對比「13個獨立 Construct（13個 Lambda / 角色）」與「單一 Custom Resource（1個 Lambda / 角色）」的架構差異（展示 92.3% 的資源減省）。
- **Custom Resource 工作原理**：說明 CloudFormation 自定義資源、Provider 框架與底層 Node.js 20.x 批次創建 IoT Thing、Certificates 並上傳 S3 桶/SSM Parameter Store 的生命週期流程。
- **憑證與私鑰分發安全**：論述儲存於 S3 和 SSM 的安全存取控制。

## 7. 機器人 SSM 指令下發與安全通道規格書 (robot_ssm.md)
審查 `SsmUserConstruct` 與 `RobotSsmConstruct`：
- **SSM 安全控制模型**：管理員/Web 端如何利用 IAM User 權限透過 SSM SendCommand 遠端執行機器人與狗（Raspberry Pi）上的指令。
- **通道安全隔離**：前綴隔離與目標裝置名稱對映設計。

---

# 執行指令
請根據以上所有要求，深入審查我提供的程式碼，並為我生成這一整套極具質感、架構嚴密、圖表美觀的系統設計文檔庫。
```
