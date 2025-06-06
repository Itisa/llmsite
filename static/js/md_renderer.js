const languageAbbreviations = {
	'javascript': 'js',
	'typescript': 'ts',
	'python': 'py',
	'java': 'java',
	'csharp': 'cs',
	'cpp': 'cpp', // C++
	'c': 'c',
	'ruby': 'rb',
	'go': 'go',
	'php': 'php',
	'html': 'html',
	'css': 'css',
	'json': 'json',
	'markdown': 'md',
	'xml': 'xml',
	'bash': 'sh',
	'shell': 'sh',
	'sql': 'sql',
	'swift': 'swift',
	'kotlin': 'kt',
	'rust': 'rs',
	'dart': 'dart',
	'scala': 'scala',
	'yaml': 'yml',
	'plaintext': 'txt'
};
function renderWithKatex(input) {
	try {
		// 正则表达式匹配行内公式 \(...\)、$...$、多行块级公式 \[...\] 以及 $$...$$
		const regex = /(\\\([\s\S]*?\\\)|\\\[[\s\S]*?\\\]|\$\$[\s\S]*?\$\$|\$[\s\S]*?\$)/g;

		// 将字符串拆分为普通文本和公式部分
		const parts = input.split(regex);
		let output = '';
		parts.forEach(part => {
			if (!part) return; // 跳过空字符串
			// 检查是否是行内公式 \(...\)
			if (part.startsWith('\\(') && part.endsWith('\\)')) {
				output += katex.renderToString(part.slice(2, -2), {
					throwOnError: true,
					displayMode: false // 行内模式
				});
			}
			// 检查是否是块级公式 $$...$$
			else if (part.startsWith('$$') && part.endsWith('$$')) {
				// 去除首尾的 $$，并去掉多余的换行符和空格
				const formula = part.slice(2, -2).trim();
				output += katex.renderToString(formula, {
					throwOnError: true,
					displayMode: true // 块级模式
				});
			}
			// 检查是否是行内公式 $...$
			else if (part.startsWith('$') && part.endsWith('$') && part.length > 1) {
				// 去除首尾的 $，并去掉多余的换行符和空格
				const formula = part.slice(1, -1).trim();
				output += katex.renderToString(formula, {
					throwOnError: true,
					displayMode: false // 行内模式
				});
			}
			// 检查是否是块级公式 \[...\]
			else if (part.startsWith('\\[') && part.endsWith('\\]')) {
				// 去除首尾的 \[ 和 \]，并去掉多余的换行符和空格
				const formula = part.slice(2, -2).trim();
				output += katex.renderToString(formula, {
					throwOnError: true,
					displayMode: true // 块级模式
				});
			}
			// 普通文本
			else {
				output += part;
			}
		});

		return output;
	} catch (error) {
		console.log(`error in katex render: ${error}`);
		return input;
	}
}

function init_renderer(rendertype="default") {
	const renderer = new marked.Renderer();
	renderer.code = function (code) {
		if (code.lang === "mermaid") {
			if (rendertype == "default") {
				return `
				<div class="mermaid-box" x-data="mermaidChart">
					<div class="mermaid-controls">
						<button @click="zoomOut">-</button>
						<span class="scale-display" x-text="\`\${Math.round(scale * 100)}%\`"></span>
						<button @click="zoomIn">+</button>
						<button @click="downloadPNG">PNG</button>
						<button @click="downloadSVG">SVG</button>
						<button @click="resetZoom">重置</button>
					</div>
					<div class="mermaid-content" @wheel.ctrl="handleWheel($event)">
						<div class="mermaid-wrapper" x-ref="wrapper" :style="\`transform: translate(\${transx}px,\${transy}px) scale(\${scale})\`">
							<div class="mermaid">
								${code.text}
							</div>
						</div>
					</div>
				</div>`;
			} else {
				return `<div class="mermaid">${code.text}</div>`;
			}

		
		}
		const validLanguage = hljs.getLanguage(code.lang) ? code.lang : 'plaintext';
		const highlightedCode = hljs.highlight(code.text, { language: validLanguage }).value;

		var topBar;
		if (rendertype == "default") {
			topBar = `
			<div class="code-top-bar">
				<span class="code-language">${validLanguage}</span>
				<div>
					<button class="copy-button" onclick="CodecopyToClipboard(this)">Copy</button>
					<button class="copy-button" onclick="DownloadCode(this, '${validLanguage}')">Download</button>
				</div>
			</div>
			`;
			
		} else {
			topBar = `
			<div class="code-top-bar">
				<span class="code-language">${validLanguage}</span>
			</div>
			`;
		}
		return `<div class="code-block">
		${topBar}
		<pre><code style="word-break: break-all; white-space: pre-wrap;" class="hljs ${validLanguage}">${highlightedCode}</code></pre>
		</div>`;
	};

	renderer.codespan = function (code) {
		const validLanguage = hljs.getLanguage(code.lang) ? code.lang : 'plaintext';
		const highlightedCode = hljs.highlight(code.text, { language: validLanguage }).value;
		return `<code style="word-break: break-all; white-space: pre-wrap;" class="hljs ${validLanguage}">${highlightedCode}</code>`;
	};

	renderer.paragraph = function(text) {
		rsp = `<p>${renderWithKatex(this.parser.parseInline(text.tokens))}</p>\n`;
		return rsp
	}
	renderer.strong = function(text) {
		rsp = `<strong>${renderWithKatex(this.parser.parseInline(text.tokens))}</strong>`;
		return rsp
	}

	renderer.text = function(token) {
		return 'tokens' in token && token.tokens ? this.parser.parseInline(token.tokens) : (token.raw);
	}

	renderer.listitem = function(item) {
		let itemBody = '';
		if (item.task) {
			const checkbox = this.checkbox({ checked: !!item.checked });
			if (item.loose) {
				if (item.tokens[0]?.type === 'paragraph') {
					item.tokens[0].text = checkbox + ' ' + item.tokens[0].text;
					if (item.tokens[0].tokens && item.tokens[0].tokens.length > 0 && item.tokens[0].tokens[0].type === 'text') {
						item.tokens[0].tokens[0].text = checkbox + ' ' + escape(item.tokens[0].tokens[0].text);
						item.tokens[0].tokens[0].escaped = true;
					}
				} else {
					item.tokens.unshift({
						type: 'text',
						raw: checkbox + ' ',
						text: checkbox + ' ',
						escaped: true,
					});
				}
			} else {
				itemBody += checkbox + ' ';
			}
		}
		itemBody += this.parser.parse(item.tokens, !!item.loose);
		return `<li>${renderWithKatex(itemBody)}</li>\n`;
	}

	renderer.tablecell = function(token) {
		const content = renderWithKatex(this.parser.parseInline(token.tokens));
		const type = token.header ? 'th' : 'td';
		const tag = token.align ? `<${type} align="${token.align}">` : `<${type}>`;
		return tag + content + `</${type}>\n`;
	}
	return renderer;
}