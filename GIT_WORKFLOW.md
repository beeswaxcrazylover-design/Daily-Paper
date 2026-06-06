# Git 版本管理

仓库根目录为 `D:\每日论文阅读`，默认分支为 `main`。

## 日常保存版本

```powershell
cd D:\每日论文阅读
git status
git add .
git commit -m "描述本次修改"
git push
```

提交前使用 `git status` 和 `git diff --staged` 确认没有密钥或私人笔记。

## 查看和回滚

查看历史：

```powershell
git log --oneline --decorate --graph
```

临时查看旧版本：

```powershell
git switch --detach <提交ID>
git switch main
```

恢复某个未提交文件：

```powershell
git restore -- path\to\file
```

撤销已推送的某次提交，保留完整历史：

```powershell
git revert <提交ID>
git push
```

不要对已上传并与他人共享的提交使用 `git reset --hard`。

## 上传 GitHub

1. 在 GitHub 新建一个空仓库，不要勾选自动创建 README、`.gitignore` 或 License。
2. 在本地执行：

```powershell
.\scripts\connect_github.ps1 -RepositoryUrl "https://github.com/用户名/仓库名.git"
```

脚本会配置 `origin` 并推送 `main`。GitHub 可能要求通过浏览器或 Personal
Access Token 完成 HTTPS 身份验证。

之后只需执行：

```powershell
git push
```

## 开发分支

较大修改建议先创建分支：

```powershell
git switch -c feature/功能名称
git add .
git commit -m "实现功能名称"
git switch main
git merge feature/功能名称
```

