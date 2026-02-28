```
frontend/
├── index.html              # HTML入口（含Google Fonts）
├── package.json            # React + Vite 依赖
├── vite.config.js          # Vite配置（含API代理到:5000）
└── src/
    ├── main.jsx            # React入口
    ├── App.jsx             # 根组件（页面路由 + Toast通知）
    ├── api.js              # API服务层（所有后端接口）
    ├── index.css           # 完整设计系统（深色主题）
    └── components/
        ├── Toast.jsx           # 通知组件
        ├── ProjectList.jsx     # 页面1：项目列表与创建
        ├── Navigation.jsx      # 工作流导航栏
        ├── SettingsModal.jsx   # 项目设置弹窗
        ├── CharacterExtract.jsx # 页面2：角色提取
        ├── DialogueAssign.jsx  # 页面3：对话分配
        ├── VoiceDesign.jsx     # 页面4：语音设计
        └── AudioGenerate.jsx   # 页面5：音频生成

```

🎨 设计特点
深色主题：深蓝色背景 + 渐变强调色 + 辉光阴影
毛玻璃导航栏：backdrop-filter: blur(16px)
微动画：fadeIn、slideUp、shimmer进度条
响应式：分栏布局在移动端自动堆叠
✅ 页面功能对应
页面	关键功能
项目列表	列出/创建(粘贴或上传文件)/删除项目，自动文本处理
角色提取	左右分栏（文本+角色），AI提取，新建/编辑/删除弹窗，AI生成描述
对话分配	左右分栏（带颜色标记），点击引语弹出气泡选择角色，AI自动分配
语音设计	表格列出角色+语音设计信息，编辑弹窗，AI语音设计，参考音频生成
音频生成	进度条+AI批量生成(异步轮询)，逐段状态/播放/重新生成，渲染下载
🚀 运行
bash
cd frontend
npm install
npm run dev
后端需在 http://127.0.0.1:5000 运行，Vite 会自动代理 /api 请求