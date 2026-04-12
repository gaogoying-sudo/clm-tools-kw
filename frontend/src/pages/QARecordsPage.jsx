import { useState, useEffect } from 'react'
import { api } from '../api'

export function QARecordsPage() {
  const [filters, setFilters] = useState({
    startDate: new Date().toISOString().slice(0, 10),
    endDate: new Date().toISOString().slice(0, 10),
    engineer: '',
    questionKey: '',
    keyword: '',
  })
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(false)
  const [expandedIds, setExpandedIds] = useState(new Set())

  const handleSearch = async () => {
    setLoading(true)
    // TODO: implement QA records API
    setRecords([])
    setLoading(false)
  }

  const toggleExpand = (id) => {
    const next = new Set(expandedIds)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    setExpandedIds(next)
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">原始问答数据</h1>

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
            <input type="text" placeholder="姓名" value={filters.engineer} onChange={e => setFilters({...filters, engineer: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
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
        <div className="flex items-center gap-3">
          <button onClick={handleSearch} disabled={loading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
            {loading ? '查询中...' : '查询'}
          </button>
          <button className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50">
            导出 CSV
          </button>
          <button className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50">
            导出 JSON
          </button>
        </div>
      </div>

      {/* Data notice */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-700">
        <strong>数据保留策略：</strong>所有问答记录不可删除，仅支持归档。保留三层数据：原始输入 (raw_input) → 转写文本 (transcribed_text) → 结构化结果 (structured_result)。
      </div>

      {/* Table */}
      {records.length === 0 && !loading && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center text-gray-400">
          设置条件后查询原始问答数据
        </div>
      )}
    </div>
  )
}
