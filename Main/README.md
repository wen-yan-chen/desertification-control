# LaTeX 论文

论文入口为 `Main/main.tex`，章节放在 `Section/`，图片放在 `Figure/`。
首页中的年份、题号、队号和标题在 `main.tex` 开头修改。正文目前为三个模型的待填写框架。

## 编译

在仓库根目录运行（需要 TeX Live / MacTeX）：

```sh
latexmk -cd -xelatex -interaction=nonstopmode -halt-on-error Main/main.tex
```

生成的 `Main/main.pdf` 和编译中间文件已忽略；`Figure/` 中的 PDF 图片仍会纳入版本管理。

## 日常协作

开始前先保存编辑器文件并检查 `git status`。有论文修改时，先明确选择自己的文件并提交本地版本，再同步：

```sh
git add -- Main
git diff --cached
git commit -m "docs: update paper"
git fetch origin
git merge --ff-only origin/main
```

若快进合并失败，保留自己的提交并检查分支差异；按仓库的 `Docs/协作同步.md` 处理。
确认合并后编译正常，再执行 `git push origin main`。不要下载 ZIP 覆盖工作目录。
队友的代码更新和论文修改可以放在同一仓库；双方修改同一文件时仍需处理冲突。
