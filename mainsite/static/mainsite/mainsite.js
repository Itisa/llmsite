function deleteCookie(name, path, domain) {
	document.cookie = name + '=; expires=Thu, 01 Jan 1970 00:00:00 GMT;' +
		(path ? '; path=' + path : '') +
		(domain ? '; domain=' + domain : '');
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
function app() {
	return {
		// 应用状态
		user: null,
		messages: [],
		titles: [],
		models: [],
		inputMessage: '',
		username: null,
		topBarContent: null,
		cid: -1,
		isEditingTitle: false,
		newTitle: null,
		selectedModel: null,
		in_talk: false,
		marked,
		renderer: new marked.Renderer(),
		show_floating_ball: true,
		floating_ball_showButtons: false,
		message_area_div: document.getElementById('message_area'),
		init() {
			this.renderer.code = function (code, language) {
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
			marked.setOptions({
				renderer: this.renderer,
			});
			// console.log("init");
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
				this.loadHistory();
				this.loadModels();
			}
		},

		logout() {
			window.location.href = urls["logout"];
		},
		userPressEnter(event){
			if (event.shiftKey) {
				return ;
			} else {
				event.preventDefault();
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
				// console.log(response)
				this.in_talk = true;
				if (!response.ok) {
					throw new Error('Network response was not ok');
				}
				let reasoning = (this.selectedModel === "deepseek_r1");
				console.log(reasoning)
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
				const reader = response.body.getReader();
				const decoder = new TextDecoder();
				let firstchunk = true;
				let in_assistant = !reasoning;
				const readChunk = () => {
					reader.read().then(({ done, value }) => {
						if (done) {
							// console.log('Stream complete');
							this.in_talk = false;
							return;
						}
						const at_bottom = this.message_area_div.scrollTop + this.message_area_div.clientHeight >= this.message_area_div.scrollHeight;
						const chunk = decoder.decode(value);
						console.log(chunk)
						// 假设服务器返回的是逐行 JSON 数据
						chunk.split('\n').forEach(line => {
							if (line.trim()) {

							try {
								const jsonData = JSON.parse(line);
								console.log(jsonData);
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
									this.messages[this.messages.length-1].content += jsonData.message;
								} else {
									if (!in_assistant){
										this.messages.push({
											id: Date.now(),
											content: "",
											role: 'assistant',
											timestamp: new Date().toLocaleTimeString(),
										});
										in_assistant = true;
									}
									this.messages[this.messages.length-1].content += jsonData.message;
								}
							} catch (error) {
								console.error('Error parsing JSON:', error);
							}

							}
						});
						if (at_bottom) {
							setTimeout(() => {
								this.message_area_div.scrollTop = this.message_area_div.scrollHeight;
							}, 0);
						}
						readChunk();  // 继续读取下一个数据块
					});
				};
				readChunk();
			})
			.catch(error => {
				console.error('Error fetching stream:', error);
			});
		},
		// 加载可选模型
		loadModels() {
			axios.get(urls["get_available_models"], {
				
			}, {
				headers: {
					"Content-Type": "application/json",
					'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
				}
			})
			.then(response => {
				// console.log(response)
				this.models = response.data.data;
				this.selectedModel = this.models[0];
			})
			.catch(error => {
				console.error('loadModels请求失败:', error);
				if (error.response.data.reason === "sessionid expires"){
					this.logout();
				}
			});
		},
		// 加载历史记录
		loadHistory() {
			axios.get(urls["get_history"],{
				headers: {
					"Content-Type": "application/json",
					'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
				}
			})
			.then(response => {
				console.log(response)
				this.titles = response.data.titles
				for (var i = 0; i < this.titles.length; i++) {
					this.titles[i].date = new Date(this.titles[i].date).toLocaleString();
					this.titles[i].title = this.titles[i].title;
				}
			})
			.catch(error => {
				console.log(error.response);
				console.error('loadHistory请求失败:', error);
				if (error.response.data.reason === "sessionid expires"){
					this.logout();
				}
			});
		},

		// 加载对话消息
		loadMessages(cid){
			if (this.in_talk) return ;
			axios.get(urls["get_communication_content"], {
				params:{
					cid: cid,
				}
			}, {
				headers: {
					"Content-Type": "application/json",
					'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
				}
			})
			.then(response => {
				// console.log(response)

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
				console.error('loadMessages请求失败:', error);
				if (error.response.data.reason === "sessionid expires"){
					this.logout();
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
			axios.post(urls["delete_communication"], {
				cid: cid,
			}, {
				headers: {
					"Content-Type": "application/json",
					'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
				}
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
				console.error('deleteCommunication请求失败:', error);
				if (error.response.data.reason === "sessionid expires"){
					this.logout();
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
			this.newTitle = this.topBarContent;
		},
		cancelEditTitle(){
			if (this.in_talk) return ;
			this.isEditingTitle = false;
			this.newTitle = null;
		},

		// 保存新标题
		saveTitle(){
			if (this.in_talk) return ;
			if (this.newTitle.length > 30) {
				alert(`标题的长度要 <= 30 (当前长度：${this.newTitle.length})`);
				return ;
			}
			axios.post(urls["change_communication_title"], {
				cid: this.cid,
				newtitle: this.newTitle,
			}, {
				headers: {
					"Content-Type": "application/json",
					'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
				}
			})
			.then(response => {
				// console.log(response)
				for (let i = 0; i < this.titles.length; i++) {
					if (this.cid === this.titles[i].id){
						this.titles[i].title = this.newTitle;
						this.topBarContent = this.titles[i].title;
						break;
					}
				}
				this.cancelEditTitle();
			})
			.catch(error => {
				console.error('saveTitle请求失败:', error);
				if (error.response.data.reason === "sessionid expires"){
					this.logout();
				}
			});
		},
		floating_ball_toggleButtons() {
			if (this.in_talk) return ;
			if (!this.floating_ball_dragging) {
				this.floating_ball_showButtons = !this.floating_ball_showButtons;
			}
		},
	}
}