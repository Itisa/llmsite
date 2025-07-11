var in_talk = false;

function downloadStringAsFile(content, filename, contentType = 'text/plain') {
	const blob = new Blob([content], { type: contentType });
	const url = URL.createObjectURL(blob);
	const a = document.createElement('a');
	a.href = url;
	a.download = filename;
	document.body.appendChild(a);
	a.click();
	setTimeout(() => {
		document.body.removeChild(a);
		URL.revokeObjectURL(url);
	}, 0);
}

function deleteCookie(name, path, domain) {
	document.cookie = name + '=; expires=Thu, 01 Jan 1970 00:00:00 GMT;' +
		(path ? '; path=' + path : '') +
		(domain ? '; domain=' + domain : '');
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

function getLanguageAbbreviation(fullName) {
	const normalized = fullName.toLowerCase().trim();
	if (languageAbbreviations.hasOwnProperty(normalized)) {
		return languageAbbreviations[normalized];
	}
	return normalized;
}
function DownloadCode(button, language) {
	const codeBlock = button.closest('.code-block').querySelector('code');
	const codeText = codeBlock.innerText;
	downloadStringAsFile(codeText,`sitedownload_${Math.floor(Math.random()*1000000000)}.${getLanguageAbbreviation(language)}`)
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

function app() {
	return {
		// 应用状态
		user: null,
		messages: [], // content, role, model(effect when role == 'assistant')
		titles: [], // id, title, date, starred
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
		show_settings: false,
		system_content: "",
		communication_temperature: "0.7", // [0, 2.0]
		communication_top_p: "0.9", // [0, 1.0]
		communication_max_tokens: "4096", // [1, 8192]
		communication_frequency_penalty: "0", // [-2.0, 2.0]
		communication_presence_penalty: "0", // [-2.0, 2.0]
		init() {
			mermaid.initialize({
				startOnLoad: false,
			});
			Alpine.data('mermaidChart', () => ({
				scale: 1,
				scaleStep: 0.1,
				minScale: 0.5,
				maxScale: 3,
				transx: 0,
				transy: 0,
				init() {
					
				},
				
				zoomIn() {
					if (this.scale < this.maxScale) {
						this.scale = Math.min(this.scale + this.scaleStep, this.maxScale);
					}
				},
				
				zoomOut() {
					if (this.scale > this.minScale) {
						this.scale = Math.max(this.scale - this.scaleStep, this.minScale);
					}
				},
				
				resetZoom() {
					this.scale = 1;
				},
				
				handleWheel(event) {
					if (event.ctrlKey) {
						event.preventDefault();
						if (event.deltaY < 0) {
							this.zoomIn();
						} else {
							this.zoomOut();
						}
					}
				},
				
				downloadPNG() {
					const svg = this.$root.querySelector('svg');
					if (!svg) return;
					
					const svgData = new XMLSerializer().serializeToString(svg);
					const canvas = document.createElement('canvas');
					const ctx = canvas.getContext('2d');
					const img = new Image();
					
					img.onload = () => {
						canvas.width = svg.width.baseVal.value * this.scale;
						canvas.height = svg.height.baseVal.value * this.scale;
						ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
						
						const pngData = canvas.toDataURL('image/png');
						this.triggerDownload(pngData, 'mermaid-diagram.png');
					};
					
					img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
				},
				
				downloadSVG() {
					const svg = this.$root.querySelector('svg');
					if (!svg) return;
					
					const svgData = new XMLSerializer().serializeToString(svg);
					const blob = new Blob([svgData], { type: 'image/svg+xml' });
					const url = URL.createObjectURL(blob);
					this.triggerDownload(url, 'mermaid-diagram.svg');
					URL.revokeObjectURL(url);
				},
				
				triggerDownload(url, filename) {
					const a = document.createElement('a');
					a.href = url;
					a.download = filename;
					document.body.appendChild(a);
					a.click();
					document.body.removeChild(a);
				}
			}));

			marked.setOptions({
				renderer: this.renderer,
			});
			this.topBarContent = "新对话";
			this.get_history();
			this.get_available_models();
			this.title_diff_days = [ // 需要确保days递增，最后一个是-1
				{name:"我的收藏",days:0},
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
		
		// 用户发送消息
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
			const uploadSystem = this.system_content;
			const uploadCid = this.cid;
			this.inputMessage = "";
			this.messages.push({
				model: '',
				content: uploadMessage,
				role: 'user',
			});
			
			let reasoning = (this.models[this.selectedModelid].type === "reasoning");
			this.in_talk = true;
			in_talk = true;
			setTimeout(() => {
				this.message_area_div.scrollTop = this.message_area_div.scrollHeight;
			}, 0);

			this.messages.push({
				model: this.models[this.selectedModelid].origin,
				content: "",
				role: 'waiting',
			});

			if (this.cid === -1) {
				this.cid = -2; // 先把转圈圈显示出来，(不是-1就会显示)
			}

			fetch(urls["talk"], {
				method: 'POST',	
				headers: {
					'Content-Type': 'application/json',
					'X-CSRFToken': this.csrftoken,
				},
				body: JSON.stringify({
					model_name: this.models[this.selectedModelid].name,
					message: uploadMessage,
					system: uploadSystem,
					cid: uploadCid,
					temperature: Number(this.communication_temperature),
					top_p: Number(this.communication_top_p),
					max_tokens: Number(this.communication_max_tokens),
					frequency_penalty: Number(this.communication_frequency_penalty),
					presence_penalty: Number(this.communication_presence_penalty),
				})
			})
			.then(response => {
				this.messages.pop()
				if(this.cid >= 0) this.update_title(this.cid);
				
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
						this.end_talk();
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
									if (firstchunk){
										if (this.cid < 0){ // 新对话 
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
		end_talk() {
			in_talk = false;
			this.in_talk = false;
			setTimeout(() => {
				mermaid.run();
			},0);
		},

		// 加载可选模型
		get_available_models() {
			$axios.get(urls["get_available_models"])
			.then(response => {
				this.models = response.data.data;
				
				const last_used_model = localStorage.getItem("last_used_model");
				if (last_used_model === null) {
					this.selectedModelid = 0;
				} else {
					this.selectedModelid = this.get_model_ind(last_used_model);
				}
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
				const status = response.data.status;
				if (status == "fail") {
					const reason = response.data.reason;
					if (reason == "no communication") {
						alert("对话不存在或已被删除");
						this.createNewChat();
					} else if (reason == "no permission") {
						alert("没有权限访问该对话");
						this.createNewChat();
					}
					return ;
				}
				let [i,j] = this.find_title_by_cid(cid);
				this.messages = response.data.messages
				this.selectedModelid = this.get_model_ind(this.titles[i][j].model);
				this.cid = cid;
				this.update_topBar();
				this.get_params(cid);
				setTimeout(() => {
					mermaid.run();
					setTimeout(() => {
						this.message_area_div.scrollTop = this.message_area_div.scrollHeight;
					},0);
				},0);
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
		
		// 收藏对话
		starCommunication(cid, b) {
			$axios.post(urls["star_communication"], {
				cid: cid,
				b: b,
			})
			.then(response => {
				const status = response.data.status;
				if (status == "fail") {
					const reason = response.data.reason;
					if (reason == "communication not found") {
						alert("对话不存在或已被删除");
					} else if (reason == "params error: b is not a boolen") {
						alert("参数错误: b 不是布尔值");
					} else if (reason == "no permission") {
						alert("没有权限访问该对话");
					}
					return ;
				}
				const rb = response.data.data;
				let [i,j] = this.find_title_by_cid(cid);
				var tmp = {...this.titles[i][j]};
				tmp.starred = rb
				this.titles[i].splice(j,1);

				if (rb) {
					this.titles[0].unshift(tmp);
				} else {
					this.titles[1].unshift(tmp);
				}
			})
			.catch(error => {
				console.log('starCommunication请求失败:')
				console.log(error);
				if (error.status === 401){
					window.location.href = urls["login"];
				}
			});
		},

		// 删除对话
		deleteCommunication(cid,title) {
			if (this.in_talk) return ;
			let yes = confirm(`确认删除  ${title} ？ 删除后将不可恢复`)
			if (!yes) return ;
			$axios.post(urls["delete_communication"], {
				cid: cid,
			})
			.then(response => {
				const status = response.data.status;
				if (status == "fail") {
					const reason = response.data.reason;
					if (reason == "communication not found") {
						alert("对话不存在或已被删除");
					} else if (reason == "no permission") {
						alert("没有权限访问该对话");
					}
					return ;
				}
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
			this.cid = -1;
			this.topBarContent = "新对话";
			this.messages = [];
			this.focusOnInput();
			this.InitParams();
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

				const status = response.data.status;
				if (status == "fail") {
					const reason = response.data.reason;
					if (reason == "communication not found") {
						alert("对话不存在或已被删除");
					} else if (reason == "no permission") {
						alert("没有权限访问该对话");
					} else if (reason == "title too long") {
						alert("标题长度超过限制(30)");
					}
					return ;
				}

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
		
		// 是否显示个人信息
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
		
		// Ctrl+K 新建对话
		UserPressK(event) {
			if (event.ctrlKey == true){
				event.preventDefault();
				this.createNewChat();
			}
		},

		//获取模型在 this.models 中的下标
		get_model_ind(model_name) {
			for (var i = 0; i < this.models.length; i++) {
				if (this.models[i].name === model_name){
					return i;
				}
			}
			return 0;
		},

		UserChangeModel(event){
			const model_name = this.models[Number(event.srcElement.value)].name;
			localStorage.setItem("last_used_model",model_name);
			event.srcElement.blur();
		},

		// 将标题排序
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
				if (line_titles[i].starred) {
					tmparr[0].push(line_titles[i]);
					continue;
				}
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
			this.titles[1].unshift(dict); //unshift 在数组开头插入元素
		},

		// 更新修改后的标题
		update_title(cid) {
			let [i,j] = this.find_title_by_cid(this.cid)
			let oldtitle = this.titles[i][j];
			this.titles[i].splice(j,1);
			oldtitle.date = new Date();
			oldtitle.title = this.topBarContent;
			if (oldtitle.starred) {
				this.titles[0].unshift(oldtitle);
			} else {
				this.titles[1].unshift(oldtitle);
			}
		},

		UserCopyMessage(event){
			let element = event.srcElement.parentElement;
			MessagecopyToClipboard(element);
			event.srcElement.src = urls["check_png"];
			setTimeout(() => {
				event.srcElement.src = urls["copybtn_png"];
			},1500);
		},

		// 获取服务器存的对话参数
		get_params(cid) {
			if (this.in_talk) return ;
			$axios.get(urls["get_params"], {
				params:{
					cid: cid,
				}
			})
			.then(response => {
				const status = response.data.status;
				if (status == "fail") {
					const reason = response.data.reason;
					if (reason == "communication not found") {
						alert("对话不存在或已被删除");
					} else if (reason == "no permission") {
						alert("没有权限访问该对话");
					}
					this.createNewChat();
					return ;
				}

				const data = JSON.parse(response.data.data)
				this.system_content = data.system;
				this.communication_temperature = data.temperature;
				this.communication_top_p = data.top_p;
				this.communication_max_tokens = data.max_tokens;
				this.communication_frequency_penalty = data.frequency_penalty;
				this.communication_presence_penalty = data.presence_penalty;
			})
			.catch(error => {
				console.log('get_params请求失败:')
				console.log(error);
				if (error.status === 401){
					window.location.href = urls["login"];
				}
			});
		},

		UserEnterSettings(event) {
			this.show_settings = true;
		},
		CloseSettings() {
			this.show_settings = false;
		},
		
		// 聚焦元素
		focusByName(name) {
			const elements = document.getElementsByName(name);
			if (elements.length > 0) {
				setTimeout(() => {
					elements[0].focus(); 
				},0)
			} else {
				console.warn(`Element with name "${name}" not found`);
			}
		},

		InitParams() {
			this.communication_temperature = 0.7;
			this.communication_top_p = 0.9;
			this.communication_max_tokens = 4096;
			this.communication_frequency_penalty = 0;
			this.communication_presence_penalty = 0;
			this.system_content = "";
		},

		UserCopy2pdf(event) {
			if (this.in_talk) return ;
			const element = event.srcElement.parentElement;
			const codeText = element.childNodes[1].textContent;
			window.open(urls["ds2pdf"] + "?c=" + encodeURIComponent(codeText),"_blank");
		}
	}
}