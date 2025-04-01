function deleteCookie(name, path, domain) {
	document.cookie = name + '=; expires=Thu, 01 Jan 1970 00:00:00 GMT;' +
		(path ? '; path=' + path : '') +
		(domain ? '; domain=' + domain : '');
}
function renderWithKatex(input) {
	// 正则表达式匹配行内公式 \(...\)、$...$、多行块级公式 \[...\] 以及 $$...$$
	const regex = /(\\\([\s\S]*?\\\)|\$[\s\S]*?\$|\\\[[\s\S]*?\\\]|\$\$[\s\S]*?\$\$)/g;

	// 将字符串拆分为普通文本和公式部分
	const parts = input.split(regex);
	let output = '';
	parts.forEach(part => {
		if (!part) return; // 跳过空字符串

		// 检查是否是行内公式 \(...\)
		if (part.startsWith('\\(') && part.endsWith('\\)')) {
			output += katex.renderToString(part.slice(2, -2), {
				throwOnError: false,
				displayMode: false // 行内模式
			});
		}
		// 检查是否是行内公式 $...$
		else if (part.startsWith('$') && part.endsWith('$') && part.length > 1) {
			// 去除首尾的 $，并去掉多余的换行符和空格
			const formula = part.slice(1, -1).trim();
			output += katex.renderToString(formula, {
				throwOnError: false,
				displayMode: false // 行内模式
			});
		}
		// 检查是否是块级公式 \[...\]
		else if (part.startsWith('\\[') && part.endsWith('\\]')) {
			// 去除首尾的 \[ 和 \]，并去掉多余的换行符和空格
			const formula = part.slice(2, -2).trim();
			output += katex.renderToString(formula, {
				throwOnError: false,
				displayMode: true // 块级模式
			});
		}
		// 检查是否是块级公式 $$...$$
		else if (part.startsWith('$$') && part.endsWith('$$')) {
			// 去除首尾的 $$，并去掉多余的换行符和空格
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

function MessagecopyToClipboard(div) {
	const codeText = div.childNodes[1].textContent;
	if (navigator.clipboard) {
		navigator.clipboard.writeText(codeText).then(() => {
			MessageshowCopiedFeedback(div);
		}).catch(err => {
			console.error('Failed to copy code: ', err);
			MessagefallbackCopyText(codeText, div);
		});
	} else {
		MessagefallbackCopyText(codeText, div);
	}
}

function MessagefallbackCopyText(text, div) {
	const textarea = document.createElement('textarea');
	textarea.value = text;
	textarea.style.position = 'fixed';
	textarea.style.opacity = 0;
	document.body.appendChild(textarea);
	textarea.select();

	try {
		const success = document.execCommand('copy');
		if (success) {
			MessageshowCopiedFeedback(div);
		} else {
			console.error('Failed to copy code using execCommand');
		}
	} catch (err) {
		console.error('Failed to copy code: ', err);
	} finally {
		document.body.removeChild(textarea);
	}
}

function MessageshowCopiedFeedback(div) {
	return ;
}


function CodecopyToClipboard(button) {
	const codeBlock = button.closest('.code-block').querySelector('code');
	const codeText = codeBlock.innerText;

	if (navigator.clipboard) {
		navigator.clipboard.writeText(codeText).then(() => {
			CodeshowCopiedFeedback(button);
		}).catch(err => {
			console.error('Failed to copy code: ', err);
			CodefallbackCopyText(codeText, button);
		});
	} else {
		CodefallbackCopyText(codeText, button);
	}
}

function CodefallbackCopyText(text, button) {
	const textarea = document.createElement('textarea');
	textarea.value = text;
	textarea.style.position = 'fixed';
	textarea.style.opacity = 0;
	document.body.appendChild(textarea);
	textarea.select();

	try {
		const success = document.execCommand('copy');
		if (success) {
			CodeshowCopiedFeedback(button);
		} else {
			console.error('Failed to copy code using execCommand');
		}
	} catch (err) {
		console.error('Failed to copy code: ', err);
	} finally {
		document.body.removeChild(textarea);
	}
}

function CodeshowCopiedFeedback(button) {
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
		const validLanguage = hljs.getLanguage(code.lang) ? code.lang : 'plaintext';
		const highlightedCode = hljs.highlight(code.text, { language: validLanguage }).value;
		const topBar = `
		<div class="code-top-bar">
		<span class="code-language">${validLanguage}</span>
		<button class="copy-button" onclick="CodecopyToClipboard(this)">Copy</button>
		</div>
		`;
		
		return `<div class="code-block">
		${topBar}
		<pre><code class="hljs ${validLanguage}">${highlightedCode}</code></pre>
		</div>`;
	};

	renderer.codespan = function (code) {
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
		messages: [], // content, role, model(effect when role == 'assistant')
		titles: [], // id, title, date
		title_diff_days: [],
		models: [], // name, type, origin
		inputMessage: '',
		username: null,
		topBarContent: "",
		cid: -1,
		isEditingTitle: false,
		oldTitle: "", // if no changes no post
		selectedModelid: null,
		in_talk: false,
		marked,
		renderer: init_renderer(),
		personal_info_showButtons: false,
		message_area_div: document.getElementById('message_area'),
		user_input_textarea: document.getElementById('user_input_textarea'),
		history_list: document.getElementById('history_list'),
		$axios,
		csrftoken,
		sidebar_hidden: false,

		init() {
			marked.setOptions({
				renderer: this.renderer,
			});
			this.topBarContent = "新对话";
			this.get_history();
			this.get_available_models();
			this.title_diff_days = [ // 需要确保days递增，最后一个是-1
				{name:"今天",days:1},
				{name:"昨天",days:2},
				{name:"7天内",days:7},
				{name:"30天内",days:30},
				{name:"其它",days:-1}, 
			]; 
			for (var i = 0; i < this.title_diff_days.length; i++) {
				this.titles.push([]);
			}
		},

		find_title_by_cid(cid) {
			for (let i = 0; i < this.titles.length; i++) {
				for (let j = 0; j < this.titles[i].length; j++){
					if (cid == this.titles[i][j].id){
						return [i,j];
					}
				}
			}
			console.log("cid not found cid: " + cid);
			return [-1,-1];
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
				model: '',
				content: uploadMessage,
				role: 'user',
			});
			console.log(this.messages)
			let reasoning = (this.models[this.selectedModelid].type === "reasoning");
			this.in_talk = true;
			setTimeout(() => {
				this.message_area_div.scrollTop = this.message_area_div.scrollHeight;
			}, 0);


			fetch(urls["talk"], {
				method: 'POST',	
				headers: {
					'Content-Type': 'application/json',
					'X-CSRFToken': this.csrftoken,
				},
				body: JSON.stringify({
					model_name: this.models[this.selectedModelid].name,
					message: uploadMessage,
					cid: this.cid,
				})
			})
			.then(response => {
				if(this.cid !== -1) this.update_title(this.cid);
				
				setTimeout(() => {this.history_list.scrollTop = 0;}, 0);

				if (!response.ok) {
					if (response.status == 401){
						window.location.href = urls["login"];
						return ;
					} else {
						throw new Error('Network response was not ok');
					}
					return ;
				}
				

				// if (this.cid === -1){ // 新对话 //////////////////////////////
				// 	this.insert_title({
				// 		id: jsonData.cid,
				// 		title: jsonData.title,
				// 		date: Date.now(),
				// 	});
				// 	this.cid = jsonData.cid;
				// 	this.update_topBar();
				// }


				setTimeout(() => {
					this.message_area_div.scrollTop = this.message_area_div.scrollHeight;
				}, 0);
				var in_assistant = false;
				var reasoning_cache = "";
				var assistant_cache = "";
				var reasoning_cache_end = true;
				var assistant_cache_end = false;
				var reasoning_end = true;
				
				if (reasoning) {
					this.messages.push({
						model: '',
						content: "",
						role: 'reasoning',
					});	
					reasoning_end = false;
					reasoning_cache_end = false;
					const reasoning_interval = setInterval(() => {
						const at_bottom = this.message_area_div.scrollTop + this.message_area_div.clientHeight >= this.message_area_div.scrollHeight - 10;
						const lennow = this.messages[this.messages.length-1].content.length;
						this.messages[this.messages.length-1].content = reasoning_cache.slice(0,lennow + 3);
						if (reasoning_cache_end && this.messages[this.messages.length-1].content.length === reasoning_cache.length) {
							reasoning_end = true;
							clearInterval(reasoning_interval);
						}
						if (at_bottom) {
							setTimeout(() => {
								this.message_area_div.scrollTop = this.message_area_div.scrollHeight;
							}, 0);
						}
					},50);
				}

				const assistant_interval = setInterval(() => {
					if (!reasoning_end) return ;
					if (!in_assistant){
						this.messages.push({
							model: this.models[this.selectedModelid].origin,
							content: "",
							role: 'assistant',
						});
						in_assistant = true;
					}
					const at_bottom = this.message_area_div.scrollTop + this.message_area_div.clientHeight >= this.message_area_div.scrollHeight - 10;
					const lennow = this.messages[this.messages.length-1].content.length;	
					this.messages[this.messages.length-1].content = assistant_cache.slice(0,lennow + 3);
					if (assistant_cache_end && this.messages[this.messages.length-1].content.length === assistant_cache.length) {
						this.in_talk = false;
						clearInterval(assistant_interval);
					}
					if (at_bottom) {
						setTimeout(() => {
							this.message_area_div.scrollTop = this.message_area_div.scrollHeight;
						}, 0);
					}
				},50);
				var firstchunk = true;
				var lastchunk = '';				
				const reader = response.body.getReader();
				const decoder = new TextDecoder();
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
									if (firstchunk){ /////////////////////////////////////
										if (this.cid === -1){ // 新对话 
											this.insert_title({
												id: jsonData.cid,
												title: jsonData.title,
												date: Date.now(),
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
				this.selectedModelid = 0;
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
				this.order_title(response.data.titles);
			})
			.catch(error => {
				console.log('get_history请求失败:');
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
				let [i,j] = this.find_title_by_cid(cid);
				this.messages = response.data.messages
				this.selectedModelid = this.get_model_ind(this.titles[i][j].model);
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
			let [i,j] = this.find_title_by_cid(this.cid)
			this.topBarContent = this.titles[i][j].title;
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
				let [i,j] = this.find_title_by_cid(cid);
				if (cid === this.cid) {
					this.createNewChat();
				}
				this.titles[i].splice(j,1);
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
			this.selectedModelid = 0;
			this.cid = -1;
			this.topBarContent = "新对话";
			this.messages = [];
			this.focusOnInput();
		},
		// 开启/关闭标题编辑
		enableEditTitle(){
			if (this.in_talk) return ;
			this.isEditingTitle = true;
			this.oldTitle = this.topBarContent;
			setTimeout(() => {document.getElementById("newTitleInput").focus();},0)
			setTimeout(() => {document.getElementById("newTitleInput").focus();},50)
		},
		cancelEditTitle(){
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
				this.update_title(this.cid);

				this.oldTitle = "";
				setTimeout(() => {this.history_list.scrollTop = 0;}, 0);
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
		focusOnInput(event=undefined) {
			if (document.activeElement !== user_input_textarea) {
				if (event !== undefined){
					event.preventDefault();
				}
				user_input_textarea.focus();
			}
		},
		hide_sidebar() {
			this.sidebar_hidden = true;
		},
		show_sidebar() {
			this.sidebar_hidden = false;
		},
		UserPressK(event) {
			if (event.ctrlKey == true){
				event.preventDefault();
				this.createNewChat();
			}
		},
		get_model_ind(model_name) {
			for (var i = 0; i < this.models.length; i++) {
				if (this.models[i].name === model_name){
					return i;
				}
			}
			return 0;
		},
		UserChangeModel(event){
			event.srcElement.blur();
		},
		order_title(line_titles){
			for (var i = 0; i < line_titles.length; i++) {
				line_titles[i].date = new Date(line_titles[i].date);
			}
			line_titles.sort((a, b) => b.date - a.date);
			let tmparr = []
			tmparr = [];
			for (var i = 0; i < this.title_diff_days.length; i++) {
				tmparr.push([]);
			}
			let ind = 0;
			let now = new Date();
			for (var i = 0; i < line_titles.length; i++) {
				let daysDifference = Math.ceil((now - line_titles[i].date) / (1000 * 60 * 60 * 24));
				while(true){
					let d = this.title_diff_days[ind].days;
					if (d == -1 || daysDifference <= d) {
						tmparr[ind].push(line_titles[i]);
						break;
					}
					ind += 1;
				}	
			}
			this.titles = tmparr;

		},
		insert_title(dict){
			this.titles[0].unshift(dict); //unshift 在数组开头插入元素
		},
		update_title(cid) {
			let [i,j] = this.find_title_by_cid(this.cid)
			let oldtitle = this.titles[i][j];
			this.titles[i].splice(j,1);
			oldtitle.date = new Date();
			oldtitle.title = this.topBarContent;
			this.titles[0].unshift(oldtitle);
		},
		UserCopyMessage(event){
			let element = event.srcElement.parentElement;
			MessagecopyToClipboard(element);
		},
	}
}