function deleteCookie(name, path, domain) {
	document.cookie = name + '=; expires=Thu, 01 Jan 1970 00:00:00 GMT;' +
		(path ? '; path=' + path : '') +
		(domain ? '; domain=' + domain : '');
}
function renderWithKatex(input) {
	// 正则表达式匹配行内公式 \(...\) 和多行块级公式 \[...\]
	const regex = /(\\\(.*?\\\)|\\\[[\s\S]*?\\\])/g;

	// 将字符串拆分为普通文本和公式部分
	const parts = input.split(regex);
	let output = '';
	parts.forEach(part => {
		if (!part) return; // 跳过空字符串

		// 检查是否是行内公式
		if (part.startsWith('\\(') && part.endsWith('\\)')) {
			output += katex.renderToString(part.slice(2, -2), {
				throwOnError: false,
				displayMode: false // 行内模式
			});
		}
		// 检查是否是块级公式
		else if (part.startsWith('\\[') && part.endsWith('\\]')) {
			// 去除首尾的 \[ 和 \]，并去掉多余的换行符和空格
			const formula = part.slice(2, -2).trim();
			output += katex.renderToString(formula, {
				throwOnError: false,
				displayMode: true // 块级模式
			});
		}
		// 普通文本
		else {
			output += part;
		}
	});

	return output;
}

function copyCodeToClipboard(button) {
	const codeBlock = button.closest('.code-block').querySelector('code');
	const codeText = codeBlock.innerText;

	if (navigator.clipboard) {
		navigator.clipboard.writeText(codeText).then(() => {
			showCopiedFeedback(button);
		}).catch(err => {
			console.error('Failed to copy code: ', err);
			fallbackCopyText(codeText, button);
		});
	} else {
		fallbackCopyText(codeText, button);
	}
}

function fallbackCopyText(text, button) {
	const textarea = document.createElement('textarea');
	textarea.value = text;
	textarea.style.position = 'fixed';
	textarea.style.opacity = 0;
	document.body.appendChild(textarea);
	textarea.select();

	try {
		const success = document.execCommand('copy');
		if (success) {
			showCopiedFeedback(button);
		} else {
			console.error('Failed to copy code using execCommand');
		}
	} catch (err) {
		console.error('Failed to copy code: ', err);
	} finally {
		document.body.removeChild(textarea);
	}
}

function showCopiedFeedback(button) {
	button.textContent = 'Copied!';
	setTimeout(() => {
		button.textContent = 'Copy';
	}, 2000);
}

const $axios = axios.create({
	headers: {
		"Content-Type": "application/json",
	}
});
const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
$axios.defaults.headers.common['X-CSRFToken'] = csrftoken;

function init_renderer() {
	const renderer = new marked.Renderer();
	renderer.code = function (code) {
		// 使用 highlight.js 高亮代码
		
		const validLanguage = hljs.getLanguage(code.lang) ? code.lang : 'plaintext';
		const highlightedCode = hljs.highlight(code.text, { language: validLanguage }).value;
		const topBar = `
		<div class="code-top-bar">
		<span class="code-language">${validLanguage}</span>
		<button class="copy-button" onclick="copyCodeToClipboard(this)">Copy</button>
		</div>
		`;
		
		return `<div class="code-block">
		${topBar}
		<pre><code class="hljs ${validLanguage}">${highlightedCode}</code></pre>
		</div>`;
	};

	renderer.codespan = function (code) {
		// 使用 highlight.js 高亮代码
		
		const validLanguage = hljs.getLanguage(code.lang) ? code.lang : 'plaintext';
		const highlightedCode = hljs.highlight(code.text, { language: validLanguage }).value;
		return `<code class="hljs ${validLanguage}">${highlightedCode}</code>`;
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
	return renderer;
}



function app() {
	return {
		// 应用状态
		user: null,
		messages: [],
		titles: [],
		models: [],
		inputMessage: '',
		username: null,
		topBarContent: "",
		cid: -1,
		isEditingTitle: false,
		oldTitle: "",
		selectedModel: null,
		in_talk: false,
		marked,
		renderer: init_renderer(),
		personal_info_showButtons: false,
		message_area_div: document.getElementById('message_area'),
		user_input_textarea: document.getElementById('user_input_textarea'),
		$axios,
		csrftoken,
		reasoning_models: ["deepseek_r1_火山云","deepseek_r1"],
		init() {
			marked.setOptions({
				renderer: this.renderer,
			});
			this.topBarContent = "新对话";
			
			if (document.cookie) {
				const cookiePairs = document.cookie.split('; ');
				cookiePairs.forEach(pair => {
					const [key, value] = pair.split('=');
					if (key==="username"){
						this.username = decodeURIComponent(value);
					}
				});
			}
			if (this.username){
				this.get_history();
				this.get_available_models();
			}
		},

		logout() {
			window.location.href = urls["logout"];
		},
		userPressEnterInSendMessage(event){
			if (!event.shiftKey) {
				event.preventDefault();
				event.srcElement.blur();
				this.sendMessage();
			}
		},
		// 发送消息
		sendMessage() {
			if (!this.inputMessage.trim()) return ;
			if (this.in_talk) return ;
			this.cancelEditTitle();
			const uploadMessage = this.inputMessage;
			this.inputMessage = "";
			this.messages.push({
				id: Date.now(),
				content: uploadMessage,
				role: 'user',
				timestamp: new Date().toLocaleTimeString()
			});
			let reasoning = this.reasoning_models.includes(this.selectedModel);
			this.in_talk = true;
			fetch(urls["talk"], {
				method: 'POST',	
			
				headers: {
					'Content-Type': 'application/json',
					'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
				},
				body: JSON.stringify({
					model_name: this.selectedModel,
					message: uploadMessage,
					timestamp: Date.now(),
					cid: this.cid,
				})
			})
			.then(response => {
				
				if (!response.ok) {
					// console.log(response);
					if (response.status == 401){
						window.location.href = urls["login"];
						return ;
					} else {
						throw new Error('Network response was not ok');
					}
					return ;
				}
				
				// console.log(reasoning)
				if (reasoning){
					this.messages.push({
						id: Date.now()-1,
						content: "",
						role: 'reasoning',
						timestamp: new Date().toLocaleTimeString(),
					});	
				} else {
					this.messages.push({
						id: Date.now(),
						content: "",
						role: 'assistant',
						timestamp: new Date().toLocaleTimeString(),
					});
				}
				setTimeout(() => {
					this.message_area_div.scrollTop = this.message_area_div.scrollHeight;
				}, 0);
				var in_assistant = false;
				var reasoning_cache = "";
				var assistant_cache = "";
				var reasoning_cache_end = true;
				var assistant_cache_end = false;
				var reasoning_end = true;


				const reader = response.body.getReader();
				const decoder = new TextDecoder();
				var firstchunk = true;
				var lastchunk = '';
				
				if (reasoning) {
					reasoning_end = false;
					reasoning_cache_end = false;
					const reasoning_interval = setInterval(() => {
						const at_bottom = this.message_area_div.scrollTop + this.message_area_div.clientHeight >= this.message_area_div.scrollHeight - 10;
						const lennow = this.messages[this.messages.length-1].content.length;
						this.messages[this.messages.length-1].content = reasoning_cache.slice(0,lennow + 15);
						if (reasoning_cache_end && this.messages[this.messages.length-1].content.length === reasoning_cache.length) {
							reasoning_end = true;
							clearInterval(reasoning_interval);
						}
						if (at_bottom) {
							setTimeout(() => {
								this.message_area_div.scrollTop = this.message_area_div.scrollHeight;
							}, 0);
						}
					},100);
				}

				const assistant_interval = setInterval(() => {
					if (!reasoning_end) return ;
					if (!in_assistant){
						this.messages.push({
							id: Date.now(),
							content: "",
							role: 'assistant',
							timestamp: new Date().toLocaleTimeString(),
						});
						in_assistant = true;
					}
					const at_bottom = this.message_area_div.scrollTop + this.message_area_div.clientHeight >= this.message_area_div.scrollHeight - 10;
					const lennow = this.messages[this.messages.length-1].content.length;	
					this.messages[this.messages.length-1].content = assistant_cache.slice(0,lennow + 15);
					if (assistant_cache_end && this.messages[this.messages.length-1].content.length === assistant_cache.length) {
						this.in_talk = false;
						clearInterval(assistant_interval);
					}
					if (at_bottom) {
						setTimeout(() => {
							this.message_area_div.scrollTop = this.message_area_div.scrollHeight;
						}, 0);
					}
				},100);
				

				const readChunk = () => {
					reader.read().then(({ done, value }) => {
						if (done) {
							assistant_cache_end = true;
							return;
						}
						
						const chunk = lastchunk + decoder.decode(value);
						lastchunk = "";
						// console.log(chunk);
						// 假设服务器返回的是逐行 JSON 数据
						chunk.split('\n').forEach(line => {
							if (line.trim()) {
								if (line[line.length-1] != "}"){
									if (lastchunk != ""){
										console.log(lastchunk);
										console.error("exist lastchunk");
									}
									lastchunk = line;
								} else {
									const jsonData = JSON.parse(line);
									// console.log(jsonData);
									if (firstchunk){
										if (this.cid === -1){ // 新对话
											this.titles.push({
												id: jsonData.cid,
												title: jsonData.title,
												date: Date.now(),
												model: this.selectedModel,
											});
											this.cid = jsonData.cid;
											this.update_topBar();
										}
										firstchunk = false;
									}
									if (jsonData.role === "reasoning") {
										reasoning_cache += jsonData.message
									} else {
										reasoning_cache_end	= true;
										assistant_cache += jsonData.message
									}
								}
							}
						});
						
						readChunk();  // 继续读取下一个数据块
					});
				};
				readChunk();
			})
			.catch(error => {
				console.log(error);
				console.log(error.message);
				this.in_talk = false;
			});
		},
		// 加载可选模型
		get_available_models() {
			$axios.get(urls["get_available_models"])
			.then(response => {
				this.models = response.data.data;
				this.selectedModel = this.models[0];
			})
			.catch(error => {
				console.log("error in get_available_models");
				console.log(error);
				if (error.status == 401) {
					window.location.href = urls["login"];
				}	
			});
		},
		// 加载历史记录
		get_history() {
			$axios.get(urls["get_history"])
			.then(response => {
				// console.log(response)
				this.titles = response.data.titles
				for (var i = 0; i < this.titles.length; i++) {
					this.titles[i].date = new Date(this.titles[i].date).toLocaleString();
					this.titles[i].title = this.titles[i].title;
				}
			})
			.catch(error => {
				console.log('get_history请求失败:')
				console.log(error);
				if (error.status === 401){
					window.location.href = urls["login"];
				}
			});
		},

		// 加载对话消息
		get_communication_content(cid){
			if (this.in_talk) return ;
			this.isEditingTitle = false;
			this.topBarContent = null;
			$axios.get(urls["get_communication_content"], {
				params:{
					cid: cid,
				}
			})
			.then(response => {
				for (var i = 0; i < this.titles.length; i++) {
					if (cid == this.titles[i].id){
						this.selectedModel = this.titles[i].model;
						break;
					}
				}

				this.messages = response.data.messages
				for (var i = 0; i < this.messages.length; i++) {
					this.messages[i].timestamp =new Date(this.messages[i].timestamp).toLocaleString();
				}
				this.cid = cid;
				this.update_topBar();
			})
			.catch(error => {
				console.log('get_communication_content请求失败:')
				console.log(error);
				if (error.status === 401){
					window.location.href = urls["login"];
				}
			});
		},

		// 更新当前对话标题
		update_topBar() {
			for (let i = 0; i < this.titles.length; i++) {
				if (this.cid === this.titles[i].id){
					this.topBarContent = this.titles[i].title;
					break;
				}
			}
		},

		deleteCommunication(cid,title) {
			if (this.in_talk) return ;
			let yes = confirm(`确认删除  ${title} ？ 删除后将不可恢复`)
			if (!yes) return ;
			$axios.post(urls["delete_communication"], {
				cid: cid,
			})
			.then(response => {
				// console.log(response)
				for (var i = 0; i < this.titles.length; i++) {
					if (cid === this.titles[i].id){
						if (cid === this.cid) {
							this.createNewChat();
						}
						this.titles.splice(i,1);
						break;
					}
				}
			})
			.catch(error => {
				console.log('deleteCommunication请求失败:')
				console.log(error);
				if (error.status === 401){
					window.location.href = urls["login"];
				}
			});
		},

		// 开启新对话
		createNewChat() {
			if (this.in_talk) return ;
			this.selectedModel = this.models[0];
			this.cid = -1;
			this.topBarContent = "新对话";
			this.messages = [];
		},
		// 开启/关闭标题编辑
		enableEditTitle(){
			if (this.in_talk) return ;
			this.isEditingTitle = true;
			this.oldTitle = this.topBarContent;
			setTimeout(() => {
				document.getElementById("newTitleInput").focus();
			})
		},
		cancelEditTitle(){ // not used
			if (this.in_talk) return ;
			this.isEditingTitle = false;
		},
		userPressEnterInEditingTitle(event){
			if (!event.shiftKey) {
				event.preventDefault();
				this.saveTitle();
			}
		},

		// 保存新标题
		saveTitle(){
			this.isEditingTitle = false;
			if (this.in_talk) return ;
			if (this.topBarContent == this.oldTitle) return ;
			if (this.topBarContent.length > 30) {
				alert(`标题的长度要 <= 30 (当前长度：${this.topBarContent.length})`);
				return ;
			}
			$axios.post(urls["change_communication_title"], {
				cid: this.cid,
				newtitle: this.topBarContent,
			})
			.then(response => {
				// console.log(response)
				for (let i = 0; i < this.titles.length; i++) {
					if (this.cid === this.titles[i].id){
						this.titles[i].title = this.topBarContent;
						this.topBarContent = this.titles[i].title;
						break;
					}
				}
				this.oldTitle = "";
			})
			.catch(error => {
				console.log("error in saveTitle请求失败");
				console.log(error);
				if (error.status == 401) {
					window.location.href = urls["login"];
				}
			});
		},
		personal_info_toggleButtons() {
			if (this.in_talk) return ;
			this.personal_info_showButtons = !this.personal_info_showButtons;
		},
		focusOnInput(event) {
			if (document.activeElement !== user_input_textarea) {
				event.preventDefault();
				user_input_textarea.focus();
			}
		},
	}
}