import { useState, useEffect } from 'react'
import { api } from '../api'

export function QARecordsPage() {
  const [filters, setFilters] = useState({
    startDate: new Date(Date.now() - 7 * 86400000).toISOString().slice(0, 10),
    endDate: new Date().toISOString().slice(0, 10),
    engineerId: '',
    questionKey: '',
    keyword: '',
  })
  const [records, setRecords] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [expandedIds, setExpandedIds] = useState(new Set())
  const [engineers, setEngineers] = useState([])

  useEffect(() => {
    api.getEngineers('').then(setEngineers).catch(() => {})
  }, [])

  const handleSearch = async (p = 1) => {
    setLoading(true)
    setPage(p)
    try {
      const params = {
        start_date: filters.startDate,
        end_date: filters.endDate,
        page: p,
        size: 50,
      }
      if (filters.engineerId) params.engineer_id = filters.engineerId
      if (filters.questionKey) params.question_key = filters.questionKey
      if (filters.keyword) params.keyword = filters.keyword

      const data = await api.getQARecords(params)
      setRecords(data.items || [])
      setTotal(data.total || 0)
    } catch (err) {
      console.error('QA records error:', err)
      setRecords([])
    }
    setLoading(false)
  }

  const toggleExpand = (id) => {
    const next = new Set(expandedIds)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    setExpandedIds(next)
  }

  const handleExportCSV = () => {
    const rows = [['日期', '工程师', '问题', '转写文本', '原始输入', '结构化结果']]
    records.forEach(r => {
      rows.push([
        r.session_date || '',
        r.engineer?.name || '',
        r.question?.title || '',
        r.transcribed_text || '',
        JSON.stringify(r.raw_input || ''),
        JSON.stringify(r.structured_result || ''),
      ])
    })
    const csv = rows.map(r => r.map(c => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n')
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `clm_qa_records_${filters.startDate}_${filters.endDate}.csv`
    a.click()
  }

  const handleExportJSON = () => {
    const blob = new Blob([JSON.stringify(records, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `clm_qa_records_${filters.startDate}_${filters.endDate}.json`
    a.click()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">原始问答数据</h1>
        <div className="flex gap-2">
          <button onClick={handleExportCSV} className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm hover:bg-gray-50">
            导出 CSV
          </button>
          <button onClick={handleExportJSON} className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm hover:bg-gray-50">
            导出 JSON
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="grid grid-cols-5 gap-4 mb-4">
          <div>
            <label className="block text-sm text-gray-600 mb-1">开始日期</label>
            <input type="date" value={filters.startDate} onChange={e => setFilters({...filters, startDate: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">结束日期</label>
            <input type="date" value={filters.endDate} onChange={e => setFilters({...filters, endDate: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">工程师</label>
            <select value={filters.engineerId} onChange={e => setFilters({...filters, engineerId: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
              <option value="">全部</option>
              {engineers.map(e => <option key={e.engineer.id} value={e.engineer.id}>{e.engineer.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">问题模板</label>
            <input type="text" placeholder="question_key" value={filters.questionKey} onChange={e => setFilters({...filters, questionKey: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">关键词</label>
            <input type="text" placeholder="搜索原始文本" value={filters.keyword} onChange={e => setFilters({...filters, keyword: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
          </div>
        </div>
        <button onClick={() => handleSearch(1)} disabled={loading}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
          {loading ? '查询中...' : '查询'}
        </button>
      </div>

      {/* Data notice */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-700">
        <strong>数据保留策略：</strong>所有问答记录不可删除，仅支持归档。保留三层数据：原始输入 (raw_input) → 转写文本 (transcribed_text) → 结构化结果 (structured_result)。
      </div>

      {/* Loading */}
      {loading && <div className="flex items-center justify-center h-32 text-gray-400">查询中...</div>}

      {/* Empty */}
      {!loading && records.length === 0 && total === 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center text-gray-400">
          设置条件后查询原始问答数据
        </div>
      )}

      {/* Results */}
      {!loading && records.length > 0 && (
        <>
          <div className="text-sm text-gray-500">共 {total} 条记录</div>
          <div className="space-y-2">
            {records.map(r => (
              <div key={r.id} className="bg-white rounded-xl shadow-sm border border-gray-200">
                <div className="px-6 py-3 flex items-center justify-between cursor-pointer hover:bg-gray-50"
                  onClick={() => toggleExpand(r.id)}>
                  <div className="flex items-center gap-4">
                    <span className="text-sm text-gray-500">{r.session_date}</span>
                    <span className="font-medium text-gray-900">{r.engineer?.name || '未知'}</span>
                    <span className="text-sm text-gray-600">{r.question?.title || '未知问题'}</span>
                    {r.question?.is_triggered && <span className="px-2 py-0.5 bg-orange-100 text-orange-700 rounded text-xs">触发题</span>}
                  </div>
                  <div className="flex items-center gap-2">
                    {r.related_task && (
                      <span className="text-xs text-gray-400">{r.related_task.dish_name}</span>
                    )}
                    <span className="text-gray-400 text-sm">{expandedIds.has(r.id) ? '▼' : '▶'}</span>
                  </div>
                </div>

                {expandedIds.has(r.id) && (
                  <div className="px-6 pb-4 border-t border-gray-100 pt-3 space-y-3">
                    {/* Raw Input */}
                    <div className="bg-gray-50 rounded-lg p-3">
                      <div className="text-xs font-medium text-gray-500 mb-1">原始输入 (raw_input)</div>
                      <pre className="text-sm text-gray-700 whitespace-pre-wrap">{r.raw_input ? JSON.stringify(r.raw_input, null, 2) : '无'}</pre>
                    </div>
                    {/* Transcribed Text */}
                    <div className="bg-blue-50 rounded-lg p-3">
                      <div className="text-xs font-medium text-blue-600 mb-1">转写文本 (transcribed_text)</div>
                      <div className="text-sm text-gray-800">{r.transcribed_text || '无'}</div>
                    </div>
                    {/* Structured Result */}
                    <div className="bg-green-50 rounded-lg p-3">
                      <div className="text-xs font-medium text-green-600 mb-1">结构化结果 (structured_result)</div>
                      <pre className="text-sm text-gray-700 whitespace-pre-wrap">{r.structured_result ? JSON.stringify(r.structured_result, null, 2) : '无'}</pre>
                    </div>
                    {/* Metadata */}
                    <div className="text-xs text-gray-400">
                      回答时间: {r.answered_at || '未提交'} · 类型: {r.question?.type || ''}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Pagination */}
          {total > 50 && (
            <div className="flex items-center justify-center gap-2">
              <button onClick={() => handleSearch(page - 1)} disabled={page <= 1}
                className="px-3 py-1 border border-gray-300 rounded disabled:opacity-50 text-sm">上一页</button>
              <span className="text-sm text-gray-500">第 {page} 页</span>
              <button onClick={() => handleSearch(page + 1)} disabled={records.length < 50}
                className="px-3 py-1 border border-gray-300 rounded disabled:opacity-50 text-sm">下一页</button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
