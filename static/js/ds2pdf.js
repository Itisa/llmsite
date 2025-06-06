const $axios = axios.create({
	headers: {
		"Content-Type": "application/json",
	}
});
const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
$axios.defaults.headers.common['X-CSRFToken'] = csrftoken;

function init(textval) {
	const rendered_div = document.getElementById("rendered_div")
	const textarea = document.getElementById('textarea');

	textarea.addEventListener('input', function(event) {
		rendered_div.innerHTML = marked.parse(event.target.value);
		setTimeout(() => {mermaid.run();},0)
	});
	textarea.value = textval;
	rendered_div.innerHTML = marked.parse(textval);
	mermaid.run();

	mermaid.initialize({
		startOnLoad: false,
	});
	marked.setOptions({
		renderer: init_renderer("ds2pdf"),
	});
}

function render_all(s) {
	return `
<!DOCTYPE html>
<html>
<head>
	<link rel="stylesheet" href="${higtlightcss_url}">
	<link rel="stylesheet" href="${ds2pdfcss_url}">
	<link rel="stylesheet" href="${katexcss_url}">
</head>
<body>
${s}
</body>
</html>
	`;
}

function saveaspdf() {
	const originalText = document.getElementById('textarea').value;
	const originalContents = document.body.innerHTML;

	document.body.innerHTML = render_all(document.getElementById('rendered_div').innerHTML);
	setTimeout(() => {
		window.print();
		document.body.innerHTML = originalContents;
		init(originalText);
	},0);
}

init("");

async function downloadAsPDF(filename = 'document.pdf') {
	const element = document.getElementById("rendered_div");
	
	// 1. PDF基础设置
	const pdf = new jsPDF({
		unit: 'mm',
		format: 'a4',
		orientation: 'portrait'
	});
	
	// 2. 边距设置（毫米）- 可自定义
	const margin = {
		left: 15,
		right: 15,
		top: 20,
		bottom: 20
	};
	
	// 3. A4尺寸和可打印区域计算
	const a4Width = 210;
	const a4Height = 297;
	const printWidth = a4Width - margin.left - margin.right;
	const printHeight = a4Height - margin.top - margin.bottom;
	
	// 4. 创建临时容器
	const tempContainer = document.createElement('div');
	tempContainer.style.position = 'absolute';
	tempContainer.style.left = '-9999px';
	tempContainer.style.width = `${printWidth}mm`;
	tempContainer.style.overflow = 'hidden';
	
	// 5. 克隆并包装内容
	const contentClone = element.cloneNode(true);
	tempContainer.appendChild(contentClone);
	document.body.appendChild(tempContainer);
	
	// 6. 转换为canvas（完整高度）
	const canvas = await html2canvas(tempContainer, {
		scale: 2,
		logging: true,
		useCORS: true,
		windowWidth: Math.floor(printWidth * 3.78),
		width: Math.floor(printWidth * 3.78),
		height: contentClone.scrollHeight,
		scrollY: 0
	});
	
	// 7. 清理临时元素
	document.body.removeChild(tempContainer);
	
	// 8. 图像参数计算
	const imgData = canvas.toDataURL('image/png');
	const imgWidthInMM = printWidth;
	const imgHeightInMM = (canvas.height * printWidth) / canvas.width;
	
	// 9. 分页与裁剪处理
	let currentPosition = 0;
	let pageCount = 0;
	
	while (currentPosition < imgHeightInMM) {
		if (pageCount > 0) {
			pdf.addPage('a4', 'portrait');
		}
		
		// 计算裁剪参数
		const remainingHeight = imgHeightInMM - currentPosition;
		const displayHeight = Math.min(printHeight, remainingHeight);
		
		// 关键：使用裁剪参数确保每页只显示对应部分
		const cropY = currentPosition * 3.78 * 2; // mm转px，考虑scale=2
		const cropHeight = displayHeight * 3.78 * 2;
		
		// 创建临时canvas进行裁剪
		const pageCanvas = document.createElement('canvas');
		pageCanvas.width = canvas.width;
		pageCanvas.height = cropHeight;
		const ctx = pageCanvas.getContext('2d');
		ctx.drawImage(
			canvas,
			0, cropY,           // 源图像裁剪位置(x,y)
			canvas.width, cropHeight, // 源图像裁剪尺寸
			0, 0,                // 目标canvas放置位置
			canvas.width, cropHeight  // 目标canvas尺寸
		);
		
		// 将裁剪后的图像添加到PDF
		pdf.addImage(
			pageCanvas.toDataURL('image/png'),
			'PNG',
			margin.left,
			margin.top,
			imgWidthInMM,
			displayHeight,
			undefined,
			'FAST'
		);
		
		currentPosition += printHeight;
		pageCount++;
	}
	
	// 10. 下载PDF
	pdf.save(filename);
}
function OpenReport() {
	document.getElementById("reportUI").style.display = "flex";
	document.getElementById("report_content").value = document.getElementById('textarea').value;
}
function CloseReport() {
	document.getElementById("reportUI").style.display = "none";
}

function report() {
	$axios.post(report_url, {
		content: document.getElementById("report_content").value,
		description: document.getElementById("report_description").value,
	})
	.then(response => {
		alert("提交成功！感谢您的Report")
		document.getElementById("reportUI").style.display = "none";
	})
	.catch(error => {
		console.log('report请求失败:')
		console.log(error);
	});
}