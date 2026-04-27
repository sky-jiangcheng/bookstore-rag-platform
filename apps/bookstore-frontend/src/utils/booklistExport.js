const EXCEL_MIME = 'application/vnd.ms-excel;charset=utf-8'

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function formatNumber(value) {
  const number = Number(value)
  return Number.isFinite(number) ? number : 0
}

function formatPrice(value) {
  return formatNumber(value).toFixed(2)
}

function formatScore(value) {
  const score = formatNumber(value)
  if (score > 1) {
    return `${Math.round(score)}%`
  }
  return `${Math.round(score * 100)}%`
}

function normalizeBooks(booklistOrBooks) {
  if (Array.isArray(booklistOrBooks)) {
    return booklistOrBooks
  }

  if (booklistOrBooks && Array.isArray(booklistOrBooks.books)) {
    return booklistOrBooks.books
  }

  if (booklistOrBooks && Array.isArray(booklistOrBooks.recommendations)) {
    return booklistOrBooks.recommendations
  }

  if (booklistOrBooks && Array.isArray(booklistOrBooks.book_list)) {
    return booklistOrBooks.book_list
  }

  return []
}

function normalizeFilename(name) {
  return String(name || '书单')
    .replace(/[\\/:*?"<>|]/g, '_')
    .trim() || '书单'
}

function buildRow(book, index) {
  const score = book.score ?? book.relevance_score ?? book.match_score ?? 0
  return {
    index: index + 1,
    title: book.title || '',
    author: book.author || '',
    publisher: book.publisher || '',
    category: book.category || '',
    price: formatPrice(book.price),
    stock: formatNumber(book.stock),
    score: formatScore(score),
    remark: book.remark || '',
    source: book.source || '',
  }
}

function buildExcelHtml(booklistOrBooks, options = {}) {
  const books = normalizeBooks(booklistOrBooks)
  const booklistName = options.booklistName || booklistOrBooks?.name || '书单'
  const rows = books.map(buildRow)
  const totalPrice = rows.reduce((sum, row) => sum + formatNumber(row.price), 0).toFixed(2)
  const generatedAt = new Date().toLocaleString('zh-CN')

  const headerCells = [
    '序号',
    '书名',
    '作者',
    '出版社',
    '分类',
    '价格',
    '库存',
    '相关度',
    '来源',
    '备注',
  ]

  const dataRows = rows.map((row) => `
      <tr>
        <td>${escapeHtml(row.index)}</td>
        <td>${escapeHtml(row.title)}</td>
        <td>${escapeHtml(row.author)}</td>
        <td>${escapeHtml(row.publisher)}</td>
        <td>${escapeHtml(row.category)}</td>
        <td>${escapeHtml(row.price)}</td>
        <td>${escapeHtml(row.stock)}</td>
        <td>${escapeHtml(row.score)}</td>
        <td>${escapeHtml(row.source)}</td>
        <td>${escapeHtml(row.remark)}</td>
      </tr>
    `).join('')

  return `<!DOCTYPE html>
<html xmlns:o="urn:schemas-microsoft-com:office:office"
      xmlns:x="urn:schemas-microsoft-com:office:excel"
      xmlns="http://www.w3.org/TR/REC-html40">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <title>${escapeHtml(booklistName)}</title>
  <!--[if gte mso 9]>
  <xml>
    <x:ExcelWorkbook>
      <x:ExcelWorksheets>
        <x:ExcelWorksheet>
          <x:Name>${escapeHtml(booklistName)}</x:Name>
          <x:WorksheetOptions>
            <x:Selected />
            <x:ProtectContents>False</x:ProtectContents>
            <x:ProtectObjects>False</x:ProtectObjects>
            <x:ProtectScenarios>False</x:ProtectScenarios>
          </x:WorksheetOptions>
        </x:ExcelWorksheet>
      </x:ExcelWorksheets>
    </x:ExcelWorkbook>
  </xml>
  <![endif]-->
  <style>
    body { font-family: Arial, "Microsoft YaHei", sans-serif; color: #1f2937; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #d1d5db; padding: 8px 10px; font-size: 14px; }
    th { background: #1f2937; color: #fff; }
    .meta td { background: #f8fafc; font-weight: 600; }
  </style>
</head>
<body>
  <table class="meta">
    <tr><td>书单名称</td><td>${escapeHtml(booklistName)}</td></tr>
    <tr><td>书籍数量</td><td>${escapeHtml(rows.length)}</td></tr>
    <tr><td>总价</td><td>¥${escapeHtml(totalPrice)}</td></tr>
    <tr><td>导出时间</td><td>${escapeHtml(generatedAt)}</td></tr>
  </table>
  <br />
  <table>
    <thead>
      <tr>${headerCells.map((cell) => `<th>${escapeHtml(cell)}</th>`).join('')}</tr>
    </thead>
    <tbody>
      ${dataRows || '<tr><td colspan="10">暂无书籍</td></tr>'}
    </tbody>
  </table>
</body>
</html>`
}

export function exportBookListToExcel(booklistOrBooks, options = {}) {
  const books = normalizeBooks(booklistOrBooks)
  if (books.length === 0) {
    throw new Error('当前没有可导出的书单')
  }

  const booklistName = normalizeFilename(options.booklistName || booklistOrBooks?.name || '书单')
  const filename = `${booklistName}_${new Date().toISOString().slice(0, 10)}.xls`
  const html = buildExcelHtml(booklistOrBooks, { ...options, booklistName })

  const blob = new Blob([`\ufeff${html}`], { type: EXCEL_MIME })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)

  return filename
}

export function exportBookListToCsv(booklistOrBooks, options = {}) {
  const books = normalizeBooks(booklistOrBooks)
  if (books.length === 0) {
    throw new Error('当前没有可导出的书单')
  }

  const rows = books.map(buildRow)
  const headers = ['序号', '书名', '作者', '出版社', '分类', '价格', '库存', '相关度', '来源', '备注']
  const csvLines = [
    headers.join(','),
    ...rows.map((row) => [
      row.index,
      row.title,
      row.author,
      row.publisher,
      row.category,
      row.price,
      row.stock,
      row.score,
      row.source,
      row.remark,
    ].map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(',')),
  ]

  const booklistName = normalizeFilename(options.booklistName || booklistOrBooks?.name || '书单')
  const filename = `${booklistName}_${new Date().toISOString().slice(0, 10)}.csv`
  const blob = new Blob([`\ufeff${csvLines.join('\n')}`], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)

  return filename
}
