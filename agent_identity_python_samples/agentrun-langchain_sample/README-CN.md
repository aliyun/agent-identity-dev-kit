# Agent Identity Python SDK 示例

基于Agent Identity Python SDK进行AgentRun出站凭据管理的示例。

## 🚀 概述

本示例展示了如何基于阿里云AgentRun集成Agent Identity SDK，实现基于OAuth2认证的工具调用，以及通过Agent身份获取阿里云STS临时凭据，并调用阿里云服务。

## ⚙️ 先决条件

### 系统要求
- Python ≥ 3.10
- pip包管理器

### 资源准备

#### 1. 支持OAuth2协议的身份提供商端点

需要准备一个支持OAuth2协议的身份提供商（IdP）作为入站身份凭据颁发者，例如github、google、阿里云等。推荐使用阿里云OAuth2应用。

获取到身份提供商的OAuth2服务端点，例如阿里云OAuth2服务端点为`https://oauth.aliyun.com`。后续步骤需要：
1. 将该OAuth2服务端点注册为AgentRun的入站凭证。
2. 使用该OAuth2服务端点的颁发JWT（JSON Web Token）能力，为终端用户颁发Token，用于访问Agent。


#### 2. 创建AgentRun大语言模型
使用您的模型服务提供商信息，例如阿里云等，在AgentRun控制台创建一个大语言模型。

![images/create_agentrun_llm.png](images/create_agentrun_llm.png)

#### 3. 创建访问AgentRun凭证
使用您的OAuth2端点，例如`https://oauth.aliyun.com`，创建Agent访问凭证，该身份提供商需要支持颁发合法的、可验证的JWT（JSON Web Token）以作为Agent的入站凭证。

在AgentRun控制台进入：其他-->凭证管理，使用您的OAuth2 URL端点创建一个入站凭证，认证类型为`JWT（JSON Web Token）`，可参照[AgentRun产品文档](https://help.aliyun.com/zh/functioncompute/fc/voucher-management?spm=a2c4g.11186623.help-menu-2508973.d_3_7.73ee14eex9CNet#9a2fdcfcfatut)。
> 备注： 需要配置的不是.well-known/openid-configuration的地址，而是其中jwks_uri对应的地址。

![创建JWT凭证](images/create_inbound_oauth_credential.png)

#### 4. 创建智能体身份

首先安装agent-identity-cli：

```bash
pip install agent-identity-cli
```

在环境变量中注入阿里云Access Key信息：
```bash
export ALIBABA_CLOUD_ACCESS_KEY_ID=<your-access-key-id>
export ALIBABA_CLOUD_ACCESS_KEY_SECRET=<your-access-key-secret>
```
注意，请确保执行命令的Access Key具备以下权限：
```json
{
  "Version": "1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "agentidentity:CreateWorkloadIdentity",
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ram:CreateRole",
        "ram:AttachPolicyToRole",
        "ram:CreatePolicy"
      ],
      "Resource": "*"
    }
  ]
}
```


运行Agent Identity CLI，创建工作负载身份和角色：

```bash
agent-identity-cli create-workload-identity --workload-identity-name <your-workload-identity-name>
```

CLI将**创建如下工作负载身份和角色**：
   - 工作负载身份名称：`<your-workload-identity-name>`
   - 角色名称：`AgentIdentityRole-${workloadIdentityName}`
   - 角色信任策略：允许来自该工作负载身份的扮演请求
   - 角色权限策略：允许该角色调用Agent Identity数据面API

进入Agent Identity控制台，创建入站身份提供商：
![创建入站身份提供商](images/create_agentidentity_inbound_provider.png)


进入工作负载身份页面，关联工作负载身份和上面创建的入站身份提供商：
![关联工作负载身份和入站身份提供商](images/associate_workload_identity_with_inbound_provider.png)


## 📦 安装和部署到AgentRun

### 1. 克隆仓库
```bash
git clone https://github.com/aliyun/agent-identity-dev-kit
cd agent_identity_python_samples/agentrun-langchain_sample
```

### 2. 安装依赖到本地
```bash
pip install -r requirements.txt -t ./python
```

### 3. 打包为zip
将当前目录打包为zip文件，用于通过zip包创建agent：
```bash
zip -r agentrun-langchain_sample.zip .
```

### 4. 创建Agent
进入AgentRun控制台，通过代码创建Agent：
![创建Agent](images/create_agent_by_code_1.png)

在设置环境变量时，增加如下环境变量：
```bash
export AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME=<your-workload-identity-name>
```
其中`MODEL_SERVICE_NAME`为创建AgentRun大语言模型时指定的模型服务名称，例如本示例名称为：`model-s75-qw`，`MODEL_NAME`为具体模型的名称，例如本示例名称为：`qwen-plus`。
![设置环境变量](images/agent_env.png)

在配置实例角色时候，确保角色权限策略包含`AgentIdentityFullAccess`：
![配置实例角色](images/agent_role.png)

配置入站访问凭证，选择在资源准备中创建的入站访问凭证。

随后点击开始部署，完成Agent部署。

### 调用

可以通过curl命令进行调用：
```bash
curl -N \
  -X POST "https://<agent-endpoint>/openai/v1/chat/completions?sessionId=<your-session-id>" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <json-web-token>" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": [
          { "type": "text", "text": "帮我写入“Helloworld”到钉钉文档，文档ID：9bN7RYPWdM***********", "user_id": "seeq" }
        ]
      }
    ],
    "stream":true
  }'


```

`<your-session-id>`为会话ID，可自定义。
`<json-web-token>`为从OAuth2身份提供商处获取的用户JWT，例如如果配置为阿里云OAuth2服务，可参照[阿里云官方文档](https://help.aliyun.com/zh/ram/access-alibaba-cloud-apis-from-a-web-application?spm=a2c4g.11186623.help-menu-28625.d_4_1_0.29707ec3U1MC9m#info-o5u-utp-d6l)，获取用户id_token（JWT）。
`<agent-endpoint>`为AgentRun部署的Agent的访问端点，可在AgentRun控制台进入Agent详情页中查看。

当访问第三方服务的时候，例如本示例中的访问钉钉文档，需要预先做好钉钉应用的接入，具体配置可以参考文档：[在Agent中安全访问钉钉](https://help.aliyun.com/zh/agentidentity/secure-access-to-dingtalk-in-agent)。

访问钉钉的授权地址需要手工输入到浏览器中，并访问授权。授权响应参考：
```bash
data: {"id": "chatcmpl-74b9c01d5100", "object": "chat.completion.chunk", "created": 1769765835, "model": "agentrun", "choices": [{"index": 0, "delta": {"role": "assistant", "content": "Please click the link to authorize Write to DingTalk document: https://agentidentitydata.cn-beijing.aliyuncs.com/oauth2/authorize?request_uri=urn:ietf:params:oauth:request_uri_parameter \n\n"}, "finish_reason": null}]}
```
授权完成后默认回跳本地应用地址，本示例中应用地址为`http://localhost:8090/callback`，可以通过环境变量`APP_REDIRECT_URI`进行替换Endpoint，例如：
```bash
export APP_REDIRECT_URI=http://localhost:8090
```
> 备注：本地应用地址需要手动配置到WorkloadIdentity中的的应用回调地址中，参考[工作负载身份管理](https://help.aliyun.com/zh/agentidentity/workload-identity-management)文档中，“为工作负载身份设置应用回调地址”章节

回跳完成后，获取回调链接中的`session_uir`参数，并主动调用`CompleteResourceTokenAuth`, 完成授权流程。调用参考SDK中`IdentityClient.confirm_user_auth`方法。
```

## 🤝 支持

关于Agent Identity SDK的问题或疑问：
- 参考[官方文档](https://help.aliyun.com/product/agent-identity)
- 联系阿里云支持
- 在仓库中提交问题

---
