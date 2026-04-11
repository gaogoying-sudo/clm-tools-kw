import { useState, useEffect, useRef } from 'react';
import { api, getAdminToken, setAdminToken } from './api.js';

const fmtTime = (s) => { const m = Math.floor(s / 60); const sec = s % 60; return m > 0 ? `${m}分${sec > 0 ? sec + '秒' : ''}` : `${sec}秒`; };
const typeLabel = (t) => ({ 0: '小份', 2: '大份', 7: '定制版' }[t] || `类型${t}`);
const fmtDate = (d) => { const dt = new Date(d + 'T00:00:00'); return dt.toLocaleDateString('zh-CN', { month: 'long', day: 'numeric', weekday: 'short' }); };
const todayStr = () => new Date().toISOString().slice(0, 10);

const ENTRY_OPTION_TO_EVENT = {
  '有道菜今天来回调了好几次': 'iterative_debugging',
  '客户今天提了明显意见': 'customer_feedback',
  '我改了一个地方，效果很明显': 'key_adjustment',
  '今天出了意料外的问题': 'abnormal_failure',
  '有个做法我觉得以后可以固定下来': 'reusable_method',
  '今天整体比较顺，没什么特别的': 'normal_day',
};

// ============================================================
// APP — Route:
// - #/            engineer home (default)
// - #/fill/:id    engineer fill flow
// - #/admin       admin console
// ============================================================
export default function App() {
  const [route, setRoute] = useState(window.location.hash || '#/');
  useEffect(() => {
    const h = () => setRoute(window.location.hash || '#/');
    window.addEventListener('hashchange', h);
    return () => window.removeEventListener('hashchange', h);
  }, []);

  if (route.startsWith('#/fill/')) {
    const id = parseInt(route.split('/')[2]);
    return <FillView sessionId={id} />;
  }
  if (route === '#/admin' || route.startsWith('#/admin/')) {
    return <AdminView />;
  }
  return <EngineerHome />;
}

// ============================================================
// ENGINEER HOME — 今日会话入口（手机优先）
// ============================================================
function EngineerHome() {
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [err, setErr] = useState('');

  const load = async () => {
    setErr('');
    setLoading(true);
    try {
      const list = await api.getTodaySessions();
      setSessions(list || []);
    } catch (e) {
      setErr(e.message || '加载失败');
    }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const handleSync = async () => {
    setSyncing(true);
    setErr('');
    try {
      await api.syncToday();
      await load();
    } catch (e) {
      setErr(e.message || '同步失败');
    }
    setSyncing(false);
  };

  const handleReset = async () => {
    if (!confirm('这会清空“今天”的会话与回答（仅开发/演示用）。确定继续？')) return;
    setResetting(true);
    setErr('');
    try {
      await api.devResetToday();
      await load();
    } catch (e) {
      setErr(e.message || '清空失败');
    }
    setResetting(false);
  };

  return (
    <div style={S.root}>
      <div style={{ ...S.shell, maxWidth: 560 }}>
        <div style={S.fillHeader}>
          <div>
            <div style={{ fontSize: 15, fontWeight: 700, color: '#1e293b' }}>录菜复盘助手</div>
            <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2 }}>工程师入口 · 今日会话</div>
          </div>
          <button style={{ ...S.btnSec, padding: '8px 10px', fontSize: 12 }} onClick={() => (window.location.hash = '#/admin')}>
            管理后台
          </button>
        </div>

        <div style={{ ...S.card, marginTop: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#1e293b' }}>开始方式</div>
              <div style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>
                先同步今日数据，再选择你的名字进入填写流程。
              </div>
            </div>
            <button style={S.syncBtnSm} onClick={handleSync} disabled={syncing}>
              {syncing ? '同步中...' : '同步今日数据'}
            </button>
            <button
              style={{ ...S.btnSec, padding: '8px 10px', fontSize: 12, opacity: resetting ? 0.7 : 1 }}
              onClick={handleReset}
              disabled={resetting}
              title="开发/演示：清空今天会话与回答"
            >
              {resetting ? '清空中...' : '清空今日'}
            </button>
          </div>
        </div>

        {err && (
          <div style={{ ...S.card, marginTop: 12, border: '1px solid #fee2e2', background: '#fff1f2' }}>
            <div style={{ fontSize: 13, color: '#991b1b', fontWeight: 600 }}>出错了</div>
            <div style={{ fontSize: 12, color: '#7f1d1d', marginTop: 4 }}>{err}</div>
          </div>
        )}

        <div style={{ ...S.secHead, marginTop: 14 }}>今日会话列表</div>

        {loading ? (
          <div style={S.empty}>加载中...</div>
        ) : sessions.length === 0 ? (
          <div style={S.empty}>今天还没有会话。先点上面的「同步今日数据」。</div>
        ) : (
          sessions.map((s) => {
            const name = s.engineer?.name || '未知工程师';
            const status = s.status || 'pending';
            const done = status === 'submitted';
            return (
              <div
                key={s.session_id}
                style={S.engRow}
                onClick={() => (window.location.hash = `#/fill/${s.session_id}`)}
              >
                <div style={{ ...S.dot, background: done ? '#22c55e' : '#3b82f6' }} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ fontSize: 14, fontWeight: 700, color: '#1e293b' }}>{name}</span>
                    <span style={{ fontSize: 11, color: '#94a3b8' }}>{s.engineer?.role || ''}</span>
                  </div>
                  <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 2 }}>
                    {s.task_count || 0}道菜 · {s.total_exec || 0}次执行
                    {(s.failed_count || 0) > 0 && <span style={{ color: '#ef4444' }}> · {s.failed_count}失败</span>}
                  </div>
                </div>
                <div style={{ fontSize: 12, color: done ? '#22c55e' : '#3b82f6', fontWeight: 700 }}>
                  {done ? '已提交' : '去填写'}
                </div>
              </div>
            );
          })
        )}

        <div style={{ height: 14 }} />
      </div>
    </div>
  );
}

// ============================================================
// ADMIN VIEW — Unified management console
// ============================================================
function AdminView() {
  const [tab, setTab] = useState('overview');
  const [date, setDate] = useState(todayStr());
  const [adminToken, setAdminTokenState] = useState(getAdminToken());

  const tabs = [
    { key: 'overview', label: '今日总览' },
    { key: 'history', label: '历史记录' },
    { key: 'candidates', label: '经验候选' },
    { key: 'questions', label: '问题管理' },
  ];

  return (
    <div style={S.root}><div style={{ ...S.shell, maxWidth: 720 }}>
      <div style={S.adminHeader}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={S.logoBox}>CLM</div>
          <div>
            <div style={{ fontSize: 16, fontWeight: 700, color: '#1e293b' }}>录菜复盘助手</div>
            <div style={{ fontSize: 11, color: '#94a3b8' }}>管理后台 · 经验回传系统</div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <input
            value={adminToken}
            onChange={(e) => setAdminTokenState(e.target.value)}
            placeholder="Admin Token（可选）"
            style={{ ...S.input, width: 200, fontSize: 12, padding: '8px 10px' }}
          />
          <button
            style={{ ...S.btn, padding: '8px 10px', fontSize: 12 }}
            onClick={() => {
              setAdminToken(adminToken);
              // 立即刷新一次，让 401 可以立刻转为正常
              window.location.reload();
            }}
          >
            保存
          </button>
        </div>
      </div>

      <div style={S.tabBar}>
        {tabs.map(t => (
          <div key={t.key} style={{ ...S.tabItem, ...(tab === t.key ? S.tabItemActive : {}) }}
            onClick={() => setTab(t.key)}>{t.label}</div>
        ))}
      </div>

      <div style={S.content}>
        {tab === 'overview' && <OverviewTab date={date} setDate={setDate} />}
        {tab === 'history' && <HistoryTab />}
        {tab === 'candidates' && <CandidatesTab />}
        {tab === 'questions' && <QuestionsTab />}
      </div>
    </div></div>
  );
}

// ============================================================
// TAB: Overview
// ============================================================
function OverviewTab({ date, setDate }) {
  const [stats, setStats] = useState(null);
  const [engineers, setEngineers] = useState([]);
  const [syncing, setSyncing] = useState(false);
  const [openSession, setOpenSession] = useState(null);
  const [sessionDetail, setSessionDetail] = useState(null);

  const load = async () => {
    try {
      const [s, e] = await Promise.all([api.getDashboard(date), api.getEngineers(date)]);
      setStats(s);
      setEngineers(e);
    } catch (e) { console.error(e); }
  };

  useEffect(() => { load(); }, [date]);

  const handleSync = async () => {
    setSyncing(true);
    try { await api.syncToday(); await load(); } catch (e) { alert('同步失败: ' + e.message); }
    setSyncing(false);
  };

  const viewSession = async (id) => {
    if (openSession === id) { setOpenSession(null); return; }
    const data = await api.getSessionAnswers(id);
    setSessionDetail(data);
    setOpenSession(id);
  };

  const isToday = date === todayStr();

  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
        <input type="date" value={date} onChange={e => setDate(e.target.value)} style={S.dateInput} />
        <span style={{ fontSize: 13, color: '#64748b' }}>{fmtDate(date)}</span>
        <div style={{ flex: 1 }} />
        {isToday && (
          <button style={S.syncBtnSm} onClick={handleSync} disabled={syncing}>
            {syncing ? '同步中...' : '同步今日数据'}
          </button>
        )}
      </div>

      {stats && (
        <div style={S.statsRow}>
          <StatBox n={stats.total_engineers} label="工程师" />
          <StatBox n={stats.sessions_today} label="会话数" color="#3b82f6" />
          <StatBox n={stats.submitted_today} label="已回收" color="#22c55e" />
          <StatBox n={`${stats.recovery_rate}%`} label="回收率"
            color={stats.recovery_rate >= 100 ? '#22c55e' : stats.recovery_rate > 0 ? '#f59e0b' : '#94a3b8'} />
          <StatBox n={stats.pending_candidates} label="待审经验" color="#8b5cf6" />
        </div>
      )}

      <div style={S.secHead}>工程师状态</div>
      {engineers.length === 0 && <div style={S.empty}>{isToday ? '点击上方「同步今日数据」开始' : '当日无数据'}</div>}

      {engineers.map(e => {
        const done = e.session_status === 'submitted';
        const hasFail = e.failed_count > 0;
        return (
          <div key={e.engineer.id} style={S.engRow}
            onClick={() => e.session_id && viewSession(e.session_id)}>
            <div style={{ ...S.dot, background: done ? '#22c55e' : e.session_status === 'pending' ? '#3b82f6' : '#e2e8f0' }} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ fontSize: 14, fontWeight: 600, color: '#1e293b' }}>{e.engineer.name}</span>
                <span style={{ fontSize: 11, color: '#94a3b8' }}>{e.engineer.role}</span>
              </div>
              {e.task_count > 0 && (
                <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 2 }}>
                  {e.task_count}道菜 · {e.total_exec}次执行
                  {hasFail && <span style={{ color: '#ef4444' }}> · {e.failed_count}失败</span>}
                </div>
              )}
            </div>
            <div style={{ fontSize: 12, color: done ? '#22c55e' : e.session_status === 'pending' ? '#3b82f6' : '#94a3b8', fontWeight: 500 }}>
              {done ? '已回收' : e.session_status === 'pushed' ? '已推送' : e.session_status === 'pending' ? '待填写' : '无会话'}
            </div>
            {e.session_id && <span style={{ fontSize: 12, color: '#cbd5e1', marginLeft: 4 }}>{openSession === e.session_id ? '↑' : '↓'}</span>}
          </div>
        );
      })}

      {openSession && sessionDetail && (
        <div style={S.detailBox}>
          <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 10 }}>
            {sessionDetail.engineer_name} · {sessionDetail.session_date}
            {sessionDetail.submitted_at && ` · 提交于 ${sessionDetail.submitted_at.slice(11, 16)}`}
            {sessionDetail.duration_seconds != null && ` · 耗时 ${sessionDetail.duration_seconds}秒`}
          </div>
          {(sessionDetail.qa_list || []).map((qa, i) => (
            <div key={i} style={{ marginBottom: 10, paddingBottom: 10, borderBottom: i < sessionDetail.qa_list.length - 1 ? '1px solid #f1f5f9' : 'none' }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: '#64748b', marginBottom: 3 }}>
                {qa.is_triggered && <span style={S.trigBadge}>触发</span>}
                {qa.question_title}
              </div>
              <div style={{ fontSize: 13, color: '#1e293b', lineHeight: 1.6 }}>
                {formatAnswer(qa)}
              </div>
            </div>
          ))}
          {sessionDetail.qa_list?.length === 0 && <div style={{ fontSize: 13, color: '#94a3b8' }}>尚未提交回答</div>}
        </div>
      )}
    </>
  );
}

function formatAnswer(qa) {
  if (qa.answer_text) return qa.answer_text;
  if (!qa.answer_json) return '未回答';
  if (Array.isArray(qa.answer_json)) return qa.answer_json.join('、');
  if (typeof qa.answer_json === 'object') {
    const parts = [];
    if (qa.answer_json.dishName) parts.push(qa.answer_json.dishName);
    if (qa.answer_json.reason) parts.push(qa.answer_json.reason);
    return parts.join(' — ') || JSON.stringify(qa.answer_json);
  }
  return String(qa.answer_json);
}

// ============================================================
// TAB: History
// ============================================================
function HistoryTab() {
  const [startDate, setStartDate] = useState(() => {
    const d = new Date(); d.setDate(d.getDate() - 7);
    return d.toISOString().slice(0, 10);
  });
  const [endDate, setEndDate] = useState(todayStr());
  const [sessions, setSessions] = useState([]);
  const [openSession, setOpenSession] = useState(null);
  const [sessionDetail, setSessionDetail] = useState(null);

  const load = async () => {
    try { const data = await api.getHistory(startDate, endDate); setSessions(data); }
    catch (e) { console.error(e); }
  };

  useEffect(() => { load(); }, [startDate, endDate]);

  const viewSession = async (id) => {
    if (openSession === id) { setOpenSession(null); return; }
    const data = await api.getSessionAnswers(id);
    setSessionDetail(data);
    setOpenSession(id);
  };

  const handleExport = () => {
    window.open(api.exportUrl(startDate, endDate), '_blank');
  };

  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14, flexWrap: 'wrap' }}>
        <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} style={S.dateInput} />
        <span style={{ color: '#94a3b8' }}>至</span>
        <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} style={S.dateInput} />
        <div style={{ flex: 1 }} />
        <button style={S.exportBtn} onClick={handleExport}>导出 CSV</button>
      </div>

      {sessions.length === 0 && <div style={S.empty}>该时间段暂无数据</div>}

      {sessions.map(s => {
        const done = s.status === 'submitted';
        return (
          <div key={s.session_id}>
            <div style={S.engRow} onClick={() => viewSession(s.session_id)}>
              <div style={{ ...S.dot, background: done ? '#22c55e' : '#e2e8f0' }} />
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ fontSize: 14, fontWeight: 600, color: '#1e293b' }}>{s.engineer?.name}</span>
                  <span style={{ fontSize: 11, color: '#94a3b8' }}>{s.session_date}</span>
                </div>
                <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 2 }}>
                  {s.task_count}道菜 · {s.total_exec}次 · {s.failed_count}失败
                  {s.duration_seconds != null && ` · 耗时${s.duration_seconds}秒`}
                </div>
              </div>
              <div style={{ fontSize: 12, color: done ? '#22c55e' : '#94a3b8', fontWeight: 500 }}>
                {done ? '已回收' : s.status === 'pending' ? '待填写' : s.status}
              </div>
            </div>

            {openSession === s.session_id && sessionDetail && (
              <div style={S.detailBox}>
                {(sessionDetail.qa_list || []).map((qa, i) => (
                  <div key={i} style={{ marginBottom: 8 }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: '#64748b', marginBottom: 2 }}>
                      {qa.is_triggered && <span style={S.trigBadge}>触发</span>}{qa.question_title}
                    </div>
                    <div style={{ fontSize: 13, color: '#1e293b', lineHeight: 1.5 }}>{formatAnswer(qa)}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </>
  );
}

// ============================================================
// TAB: Candidates
// ============================================================
function CandidatesTab() {
  const [candidates, setCandidates] = useState([]);
  const [filter, setFilter] = useState('all');

  const load = async () => {
    const params = {};
    if (filter !== 'all') params.status = filter;
    const d = await api.getCandidates(params);
    setCandidates(d.items || []);
  };

  useEffect(() => { load(); }, [filter]);

  const updateCandidate = async (id, status) => {
    await api.updateCandidate(id, { status, reviewed_by: '管理员' });
    await load();
  };

  const catLabel = { experience: '经验', failure_case: '失败案例', tuning_record: '调优', customer_pref: '客户反馈', delivery_issue: '交付问题', rule_candidate: '规则', template_patch: '模板', daily_record: '日常' };
  const catColor = { failure_case: '#dc2626', experience: '#2563eb', rule_candidate: '#7c3aed', tuning_record: '#0891b2', customer_pref: '#ea580c' };

  return (
    <>
      <div style={{ display: 'flex', gap: 6, marginBottom: 14, flexWrap: 'wrap' }}>
        {['all', 'draft', 'pending_review', 'verified', 'invalid'].map(f => (
          <button key={f} style={{ ...S.filterBtn, ...(filter === f ? S.filterBtnActive : {}) }}
            onClick={() => setFilter(f)}>
            {{ all: '全部', draft: '草稿', pending_review: '待审', verified: '已确认', invalid: '无效' }[f]}
          </button>
        ))}
      </div>

      {candidates.length === 0 && <div style={S.empty}>暂无经验候选</div>}

      {candidates.map(c => (
        <div key={c.id} style={S.candidateCard}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: '#475569' }}>{c.engineer_name} · {c.session_date}</span>
            <span style={{ ...S.catBadge, color: catColor[c.category] || '#64748b' }}>
              {catLabel[c.category] || c.category}
            </span>
          </div>
          <div style={{ fontSize: 14, color: '#1e293b', lineHeight: 1.6, marginBottom: 8 }}>{c.summary || '无摘要'}</div>
          <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            {c.status === 'draft' && <>
              <button style={S.miniBtn} onClick={() => updateCandidate(c.id, 'pending_review')}>标记待审</button>
              <button style={{ ...S.miniBtn, color: '#dc2626' }} onClick={() => updateCandidate(c.id, 'invalid')}>无效</button>
            </>}
            {c.status === 'pending_review' && <>
              <button style={{ ...S.miniBtn, background: '#eff6ff', color: '#2563eb' }} onClick={() => updateCandidate(c.id, 'verified')}>确认有效</button>
              <button style={{ ...S.miniBtn, color: '#dc2626' }} onClick={() => updateCandidate(c.id, 'invalid')}>无效</button>
            </>}
            {c.status === 'verified' && <span style={{ fontSize: 12, color: '#22c55e' }}>✓ 已确认 {c.reviewed_by && `· ${c.reviewed_by}`}</span>}
            {c.status === 'invalid' && <span style={{ fontSize: 12, color: '#94a3b8' }}>已标记无效</span>}
          </div>
        </div>
      ))}
    </>
  );
}

// ============================================================
// TAB: Questions management
// ============================================================
function QuestionsTab() {
  const [questions, setQuestions] = useState([]);
  const [editing, setEditing] = useState(null);
  const [adding, setAdding] = useState(false);

  const load = async () => {
    try { const data = await api.getQuestions(); setQuestions(data); }
    catch (e) { console.error(e); }
  };

  useEffect(() => { load(); }, []);

  const handleToggle = async (q) => {
    await api.updateQuestion(q.id, { is_active: !q.is_active });
    await load();
  };

  const handleDelete = async (q) => {
    if (!confirm(`确定删除「${q.title}」？`)) return;
    await api.deleteQuestion(q.id);
    await load();
  };

  const handleSave = async (data, isNew) => {
    if (isNew) { await api.createQuestion(data); }
    else { await api.updateQuestion(data.id, data); }
    setEditing(null);
    setAdding(false);
    await load();
  };

  const typeLabels = { single: '单选', multi: '多选', open: '开放', anchor: '锚定菜品' };
  const nodeLabels = { entry: '入口', branch: '分支', trigger: '触发' };

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
        <div style={S.secHead}>问题模板 <span style={S.countBadge}>{questions.length}</span></div>
        <button style={S.addBtn} onClick={() => { setAdding(true); setEditing(null); }}>+ 新增问题</button>
      </div>

      {adding && <QuestionForm onSave={d => handleSave(d, true)} onCancel={() => setAdding(false)} />}

      {questions.map(q => (
        <div key={q.id}>
          {editing === q.id ? (
            <QuestionForm question={q} onSave={d => handleSave({ ...d, id: q.id }, false)} onCancel={() => setEditing(null)} />
          ) : (
            <div style={{ ...S.qRow, opacity: q.is_active ? 1 : 0.5 }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                  <span style={S.qKey}>{q.question_key}</span>
                  <span style={S.qType}>{typeLabels[q.question_type] || q.question_type}</span>
                  {q.node_type && <span style={{ ...S.qType, background: q.node_type === 'entry' ? '#dbeafe' : q.node_type === 'trigger' ? '#fef3c7' : '#f1f5f9' }}>{nodeLabels[q.node_type] || q.node_type}</span>}
                  {q.is_triggered && <span style={S.trigBadge}>触发</span>}
                  {!q.is_active && <span style={{ ...S.trigBadge, background: '#fee2e2', color: '#dc2626' }}>已禁用</span>}
                </div>
                <div style={{ fontSize: 13, color: '#1e293b', marginTop: 4, lineHeight: 1.5 }}>{q.title}</div>
                {q.options && <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2 }}>选项: {q.options.join(' | ')}</div>}
              </div>
              <div style={{ display: 'flex', gap: 4, flexShrink: 0 }}>
                <button style={S.miniBtn} onClick={() => { setEditing(q.id); setAdding(false); }}>编辑</button>
                <button style={S.miniBtn} onClick={() => handleToggle(q)}>{q.is_active ? '禁用' : '启用'}</button>
                <button style={{ ...S.miniBtn, color: '#dc2626' }} onClick={() => handleDelete(q)}>删除</button>
              </div>
            </div>
          )}
        </div>
      ))}
    </>
  );
}

function QuestionForm({ question, onSave, onCancel }) {
  const [form, setForm] = useState({
    question_key: question?.question_key || '',
    question_type: question?.question_type || 'single',
    title: question?.title || '',
    subtitle: question?.subtitle || '',
    options: question?.options ? question.options.join('\n') : '',
    placeholder: question?.placeholder || '',
    is_triggered: question?.is_triggered || false,
    trigger_rule: question?.trigger_rule || '',
    trigger_priority: question?.trigger_priority || 0,
    sort_order: question?.sort_order || 0,
    is_active: question?.is_active !== false,
  });

  const set = (k, v) => setForm(p => ({ ...p, [k]: v }));

  const handleSubmit = () => {
    if (!form.question_key || !form.title) { alert('请填写问题标识和标题'); return; }
    const data = {
      ...form,
      options: form.options.trim() ? form.options.trim().split('\n').map(s => s.trim()).filter(Boolean) : null,
      trigger_priority: parseInt(form.trigger_priority) || 0,
      sort_order: parseInt(form.sort_order) || 0,
    };
    onSave(data);
  };

  return (
    <div style={S.formBox}>
      <div style={S.formRow}>
        <label style={S.formLabel}>标识 (key)</label>
        <input style={S.formInput} value={form.question_key} onChange={e => set('question_key', e.target.value)}
          placeholder="如 q1, q_fail" disabled={!!question} />
      </div>
      <div style={S.formRow}>
        <label style={S.formLabel}>类型</label>
        <select style={S.formInput} value={form.question_type} onChange={e => set('question_type', e.target.value)}>
          <option value="single">单选</option>
          <option value="multi">多选</option>
          <option value="open">开放题</option>
          <option value="anchor">锚定菜品</option>
        </select>
      </div>
      <div style={S.formRow}>
        <label style={S.formLabel}>问题标题</label>
        <input style={S.formInput} value={form.title} onChange={e => set('title', e.target.value)} />
      </div>
      <div style={S.formRow}>
        <label style={S.formLabel}>副标题</label>
        <input style={S.formInput} value={form.subtitle} onChange={e => set('subtitle', e.target.value)} />
      </div>
      {(form.question_type === 'single' || form.question_type === 'multi') && (
        <div style={S.formRow}>
          <label style={S.formLabel}>选项 (每行一个)</label>
          <textarea style={{ ...S.formInput, minHeight: 80 }} value={form.options}
            onChange={e => set('options', e.target.value)} />
        </div>
      )}
      {form.question_type === 'open' && (
        <div style={S.formRow}>
          <label style={S.formLabel}>占位提示</label>
          <textarea style={{ ...S.formInput, minHeight: 60 }} value={form.placeholder}
            onChange={e => set('placeholder', e.target.value)} />
        </div>
      )}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        <label style={{ fontSize: 13, display: 'flex', alignItems: 'center', gap: 4 }}>
          <input type="checkbox" checked={form.is_triggered} onChange={e => set('is_triggered', e.target.checked)} />
          触发题
        </label>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <label style={{ fontSize: 12, color: '#64748b' }}>排序</label>
          <input type="number" style={{ ...S.formInput, width: 60 }} value={form.sort_order}
            onChange={e => set('sort_order', e.target.value)} />
        </div>
      </div>
      {form.is_triggered && (
        <div style={S.formRow}>
          <label style={S.formLabel}>触发规则标识</label>
          <input style={S.formInput} value={form.trigger_rule} onChange={e => set('trigger_rule', e.target.value)}
            placeholder="如 has_failed_task" />
        </div>
      )}
      <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
        <button style={S.saveBtnPri} onClick={handleSubmit}>{question ? '保存修改' : '创建问题'}</button>
        <button style={S.saveBtnSec} onClick={onCancel}>取消</button>
      </div>
    </div>
  );
}

// ============================================================
// FILL VIEW — 节点式问题流
// ============================================================
function FillView({ sessionId }) {
  const [session, setSession] = useState(null);
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState({});
  const [rootEventType, setRootEventType] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const startTime = useRef(Date.now());

  useEffect(() => {
    api.getSession(sessionId).then(s => {
      setSession(s);
      setRootEventType(s.root_event_type || null);
    }).catch(e => alert('加载失败: ' + e.message));
  }, [sessionId]);

  if (!session) return <div style={S.root}><div style={{ ...S.shell, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><p style={{ color: '#94a3b8' }}>加载中...</p></div></div>;

  if (done || session.status === 'submitted') {
    return (
      <div style={S.root}><div style={{ ...S.shell, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center', padding: 40 }}>
          <div style={S.successCircle}>✓</div>
          <h2 style={{ fontSize: 20, fontWeight: 700, color: '#1e293b', margin: '0 0 8px' }}>回传完成</h2>
          <p style={{ fontSize: 14, color: '#64748b', margin: 0 }}>{session.engineer.name}，你的今日经验已成功回收。</p>
        </div>
      </div></div>
    );
  }

  const tasks = session.tasks || [];
  const allQuestions = session.questions || [];
  const rt = rootEventType || session.root_event_type;

  const visibleQuestions = allQuestions.filter(q => {
    if (q.node_type === 'entry') return true;
    if (q.node_type === 'trigger' || q.source_type === 'trigger') return true;
    if (!q.related_event_type) return true;
    return q.related_event_type === rt;
  }).sort((a, b) => (a.display_order || a.sort_order || 0) - (b.display_order || b.sort_order || 0));

  const totalSteps = visibleQuestions.length + 1;
  const progress = (step + 1) / totalSteps;

  const onAnswer = (q, v) => {
    setAnswers(p => ({ ...p, [q.question_key]: v }));
    if (q.question_key === 'q_entry' && typeof v === 'string') {
      setRootEventType(ENTRY_OPTION_TO_EVENT[v] || null);
    }
  };

  const canNext = () => {
    if (step === 0) return true;
    const q = visibleQuestions[step - 1];
    if (!q) return true;
    const a = answers[q.question_key];
    if (q.question_type === 'open') return a && String(a).trim().length > 0;
    if (q.question_type === 'single') return !!a;
    if (q.question_type === 'multi') return a && a.length > 0;
    if (q.question_type === 'anchor') return a && a.taskId;
    return true;
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    const duration = Math.round((Date.now() - startTime.current) / 1000);
    const answerList = visibleQuestions.map(q => {
      const a = answers[q.question_key];
      const base = { question_key: q.question_key };
      if (q.question_type === 'open') return { ...base, answer_type: 'text', answer_text: a || '' };
      if (q.question_type === 'single') return { ...base, answer_type: 'single', answer_json: a };
      if (q.question_type === 'multi') return { ...base, answer_type: 'multi', answer_json: a || [] };
      if (q.question_type === 'anchor') return { ...base, answer_type: 'anchor', answer_json: a, related_task_id: a?.taskId || null };
      return { ...base, answer_type: 'text', answer_text: String(a || '') };
    }).filter(a => a.answer_text || a.answer_json);

    try {
      await api.submitAnswers(sessionId, { answers: answerList, duration_seconds: duration });
      setDone(true);
    } catch (e) { alert('提交失败: ' + e.message); }
    setSubmitting(false);
  };

  const currentQ = visibleQuestions[step - 1];

  return (
    <div style={S.root}><div style={S.shell}>
      <div style={S.fillHeader}>
        <div style={{ fontSize: 15, fontWeight: 600, color: '#1e293b' }}>录菜复盘助手</div>
        <div style={{ fontSize: 11, color: '#94a3b8' }}>{session.engineer.name} · CLM Bot</div>
      </div>
      <div style={S.progOuter}><div style={{ ...S.progInner, width: `${progress * 100}%` }} /></div>

      <div style={S.body}>
        <div style={S.bubble}>
          <div style={S.botAv}>CLM</div>
          <div style={{ flex: 1, minWidth: 0 }}>
            {step === 0 ? <TaskSummary engineer={session.engineer} tasks={tasks} /> :
              <QCard q={currentQ} a={answers[currentQ?.question_key]}
                onA={v => onAnswer(currentQ, v)} tasks={tasks} />}
          </div>
        </div>
      </div>

      <div style={S.bottom}>
        <div style={S.stepLabel}>
          {step === 0 ? '任务摘要' : `问题 ${step}/${visibleQuestions.length}`}
          {currentQ?.is_triggered && <span style={{ ...S.trigBadge, marginLeft: 6 }}>条件触发</span>}
        </div>
        <div style={S.btns}>
          {step > 0 && <button style={S.btnSec} onClick={() => setStep(step - 1)}>上一步</button>}
          {step < totalSteps - 1 ? (
            <button style={{ ...S.btnPri, opacity: canNext() ? 1 : 0.35 }}
              onClick={() => canNext() && setStep(step + 1)}>{step === 0 ? '开始' : '下一题'}</button>
          ) : (
            <button style={{ ...S.btnGreen, opacity: canNext() && !submitting ? 1 : 0.35 }}
              onClick={() => canNext() && !submitting && handleSubmit()}>{submitting ? '提交中...' : '提交回传'}</button>
          )}
        </div>
      </div>
    </div></div>
  );
}

// ============================================================
// TASK SUMMARY
// ============================================================
function TaskSummary({ engineer, tasks }) {
  const [exp, setExp] = useState(null); // 仅用于“备菜须知”额外展开
  const [expandedId, setExpandedId] = useState(null); // 菜品卡片展开/收起
  const total = tasks.length;
  const totalExec = tasks.reduce((s, t) => s + t.exec_count, 0);
  const failed = tasks.filter(t => t.status === 'failed').length;
  const passed = tasks.filter(t => t.status !== 'failed').length;

  const top = (() => {
    if (!tasks.length) return null;
    return [...tasks].sort((a, b) => (b.exec_count || 0) - (a.exec_count || 0))[0];
  })();

  const summaryText = (() => {
    if (!tasks.length) return '今天没有录菜数据。';
    const failPart = failed > 0 ? `其中失败 ${failed} 道（建议优先复盘失败/高频的菜）。` : '无失败任务。';
    const topPart = top ? `最高频：${top.dish_name} ×${top.exec_count || 0}` : '';
    const abnormal = tasks.filter(t => t.has_abnormal).length;
    const abnormalPart = abnormal > 0 ? `异常提示 ${abnormal} 条。` : '';
    return `今日共 ${total} 道菜，累计执行 ${totalExec} 次；${failPart} ${topPart}${abnormalPart ? `；${abnormalPart}` : ''}`;
  })();

  const keyBadges = (t) => {
    const badges = [];
    if ((t.exec_count || 0) >= 10) badges.push({ text: `高频×${t.exec_count}`, bg: '#eff6ff', fg: '#2563eb' });
    if (t.status === 'failed') badges.push({ text: '失败', bg: '#fef2f2', fg: '#dc2626' });
    if (t.customer_name) badges.push({ text: '客户', bg: '#faf5ff', fg: '#7c3aed' });
    if (t.recipe_type === 7) badges.push({ text: '定制', bg: '#fff7ed', fg: '#c2410c' });
    if (t.has_abnormal) badges.push({ text: '异常', bg: '#fff7ed', fg: '#b45309' });
    return badges.slice(0, 3);
  };

  const execDots = (count, failedFlag) => {
    const n = Math.max(0, Number(count || 0));
    const cap = 18;
    const show = Math.min(n, cap);
    const dots = [];
    for (let i = 0; i < show; i++) {
      const isLast = i === show - 1 && n <= cap;
      dots.push(
        <span
          key={i}
          style={{
            width: 7,
            height: 7,
            borderRadius: 999,
            display: 'inline-block',
            background: failedFlag && isLast ? '#ef4444' : '#3b82f6',
            opacity: failedFlag && isLast ? 1 : 0.85,
          }}
          title={`第${i + 1}次`}
        />
      );
    }
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: 5, flexWrap: 'wrap' }}>
        {dots}
        {n > cap && <span style={{ fontSize: 11, color: '#94a3b8' }}>+{n - cap}</span>}
      </div>
    );
  };

  return (
    <div style={S.card}>
      <div style={S.cardHead}>
        <div style={S.cardTitle}>今日复盘摘要</div>
        <div style={S.cardSub}>{engineer.name} · {new Date().toLocaleDateString('zh-CN')} · {passed}通过 / {failed}失败</div>
      </div>
      <div style={S.statsRow}>
        <StatBox n={total} label="道菜" />
        <StatBox n={totalExec} label="次执行" />
        <StatBox n={failed} label="失败" color={failed > 0 ? '#dc2626' : '#16a34a'} />
      </div>

      {tasks.map((t, i) => (
        <div key={t.id} style={{ ...S.taskCard, borderLeft: t.status === 'failed' ? '3px solid #ef4444' : '3px solid #22c55e' }}>
          <div
            style={S.taskHead}
            onClick={() => setExpandedId(expandedId === t.id ? null : t.id)}
          >
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                <div style={S.taskName}>{t.dish_name}</div>
                {keyBadges(t).map((b, idx) => (
                  <span key={idx} style={{ fontSize: 11, padding: '2px 6px', borderRadius: 999, background: b.bg, color: b.fg, fontWeight: 700 }}>
                    {b.text}
                  </span>
                ))}
              </div>
              <div style={S.taskMeta}>recipe#{t.recipe_id} · v{t.recipe_version} · {typeLabel(t.recipe_type)} · {fmtTime(t.cooking_time)}</div>
            </div>
            <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
              <span style={{ ...S.statusBadge, background: t.status === 'failed' ? '#fef2f2' : '#f0fdf4', color: t.status === 'failed' ? '#dc2626' : '#16a34a' }}>{t.status === 'failed' ? '失败' : '通过'}</span>
              <span style={S.execBadge}>×{t.exec_count}</span>
              <span style={{ fontSize: 12, color: '#cbd5e1', marginLeft: 4 }}>{expandedId === t.id ? '收起' : '展开'}</span>
            </div>
          </div>

          {/* 过程感：每次执行进展（点阵） */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 6, paddingLeft: 2 }}>
            <div style={{ fontSize: 12, color: '#64748b', width: 72, flexShrink: 0 }}>执行进展</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              {execDots(t.exec_count, t.status === 'failed')}
            </div>
            <div style={{ fontSize: 12, color: '#94a3b8', flexShrink: 0 }}>
              {t.exec_time ? `最近 ${t.exec_time}` : ''}
            </div>
          </div>

          {/* 默认隐藏：点卡片后“咔嚓展开”看到瀑布流数据 */}
          {expandedId === t.id && (
            <>
              <div style={S.ctxRow}>
                <span style={S.ctxItem}>{t.customer_name || '—'}</span>
                <span style={S.ctxItem}>{t.device_id || '—'}</span>
                <span style={S.ctxItem}>{t.exec_time || '—'}</span>
              </div>

              <div style={S.sec}>
                <div style={S.secTitle}>执行过程</div>
                <div style={{ fontSize: 12, color: '#475569', lineHeight: 1.7 }}>
                  <div>今天这道菜共执行 <b>{t.exec_count || 0}</b> 次{t.exec_time ? `，最近一次约在 <b>${t.exec_time}</b>` : ''}。</div>
                  <div style={{ marginTop: 6 }}>{execDots(t.exec_count, t.status === 'failed')}</div>
                  {t.status === 'failed' && <div style={{ marginTop: 6, color: '#dc2626', fontWeight: 700 }}>提示：该菜存在失败记录，建议优先说明失败发生的阶段与调整动作。</div>}
                </div>
              </div>

              <div style={S.sec}>
                <div style={S.secTitle}>功率轨迹</div>
                <div style={S.powerRow}>
                  {(t.power_trace || []).length === 0 && <span style={{ fontSize: 12, color: '#94a3b8' }}>暂无</span>}
                  {(t.power_trace || []).map((p, j) => (
                    <span key={j} style={{ display: 'inline-flex', alignItems: 'center' }}>
                      {j > 0 && <span style={{ color: '#cbd5e1', fontSize: 12, margin: '0 3px' }}> → </span>}
                      <span style={{ fontSize: 13, fontWeight: 600, color: '#1e3a5f', fontFamily: 'monospace' }}>{p.power / 1000}kW</span>
                      <span style={{ fontSize: 10, color: '#94a3b8', marginLeft: 2 }}>@{p.time}s</span>
                    </span>
                  ))}
                </div>
              </div>

              <div style={S.sec}>
                <div style={S.secTitle}>投料时序</div>
                {(t.ingredients_timeline || []).length === 0 && <div style={{ fontSize: 12, color: '#94a3b8' }}>暂无</div>}
                {(t.ingredients_timeline || []).map((ing, j) => (
                  <div key={j} style={{ display: 'flex', alignItems: 'center', gap: 8, minHeight: 20 }}>
                    <span style={{ width: 30, fontSize: 10, color: '#94a3b8', textAlign: 'right', fontFamily: 'monospace', flexShrink: 0 }}>{ing.time}s</span>
                    <span style={{ width: 6, height: 6, borderRadius: 3, background: ing.auto ? '#3b82f6' : '#f59e0b', flexShrink: 0 }} />
                    <span style={{ fontSize: 12, color: '#475569' }}>
                      <b>{ing.name}</b> {ing.dosage}{ing.unit}
                      <span style={{ fontSize: 10, fontWeight: 700, color: ing.auto ? '#3b82f6' : '#f59e0b', marginLeft: 4 }}>{ing.auto ? '自动' : '手动'}</span>
                    </span>
                  </div>
                ))}
              </div>

              {(t.modifications || []).length > 0 && (
                <div style={S.sec}>
                  <div style={{ ...S.secTitle, color: '#dc2626' }}>调整记录 ({t.modifications.length})</div>
                  {t.modifications.map((m, j) => <div key={j} style={{ fontSize: 12, color: '#64748b', lineHeight: 1.6, paddingLeft: 4 }}>↳ {m}</div>)}
                </div>
              )}

              {exp === i && (t.ingredient_notes || []).length > 0 && (
                <div style={S.sec}>
                  <div style={S.secTitle}>备菜须知</div>
                  {t.ingredient_notes.map((n, j) => <div key={j} style={{ fontSize: 12, color: '#475569', lineHeight: 1.6 }}>{n.index}. {n.desc}</div>)}
                </div>
              )}
              {(t.ingredient_notes || []).length > 0 && (
                <div style={S.expandBtn} onClick={(e) => { e.stopPropagation(); setExp(exp === i ? null : i); }}>
                  {exp === i ? '收起 ↑' : `备菜须知 (${t.ingredient_notes.length}) ↓`}
                </div>
              )}

              {t.has_abnormal && <div style={S.abnormal}>⚠ 检测到异常：执行{t.exec_count}次，存在多次参数调整</div>}
            </>
          )}
        </div>
      ))}

      <div style={{ marginTop: 12, padding: '10px 12px', borderRadius: 12, border: '1px solid #e2e8f0', background: '#ffffff' }}>
        <div style={{ fontSize: 12, color: '#64748b', fontWeight: 800, marginBottom: 6 }}>当日小结（无需大模型）</div>
        <div style={{ fontSize: 13, color: '#0f172a', lineHeight: 1.65 }}>{summaryText}</div>
        <div style={{ marginTop: 6, fontSize: 11, color: '#94a3b8' }}>
          注：当前小结基于规则生成（频次/失败/异常等）。未来可在“提交后”引入大模型生成更范式化的经验摘要（不影响基础流程）。
        </div>
      </div>

      <div style={S.footNote}>以上数据为系统自动汇总。准备好了就点底部「开始」继续。</div>
    </div>
  );
}

// ============================================================
// QUESTION CARD (with trigger context)
// ============================================================
function QCard({ q, a, onA, tasks }) {
  if (!q) return null;
  return (
    <div style={S.card}>
      {q.trigger_context && (
        <div style={S.trigContextBanner}>
          <div style={{ fontSize: 11, fontWeight: 600, color: '#92400e', marginBottom: 2 }}>系统检测到</div>
          <div style={{ fontSize: 13, color: '#78350f', lineHeight: 1.5 }}>{q.trigger_context}</div>
        </div>
      )}
      {q.question_type === 'single' && <SingleQ q={q} a={a} onA={onA} />}
      {q.question_type === 'multi' && <MultiQ q={q} a={a} onA={onA} />}
      {q.question_type === 'open' && <OpenQ q={q} a={a} onA={onA} />}
      {q.question_type === 'anchor' && <AnchorQ q={q} a={a} onA={onA} tasks={tasks} />}
    </div>
  );
}

function SingleQ({ q, a, onA }) {
  return (
    <>
      <div style={S.qTitle}>{q.title}</div>
      <div style={S.opts}>{(q.options || []).map((o, i) => (
        <div key={i} style={{ ...S.opt, ...(a === o ? S.optSel : {}) }} onClick={() => onA(o)}>
          <div style={{ ...S.radio, ...(a === o ? S.radioSel : {}) }}>{a === o && <div style={S.radioDot} />}</div><span>{o}</span>
        </div>
      ))}</div>
    </>
  );
}

function MultiQ({ q, a, onA }) {
  const sel = a || [];
  const toggle = o => onA(sel.includes(o) ? sel.filter(x => x !== o) : [...sel, o]);
  return (
    <>
      <div style={S.qTitle}>{q.title}</div>
      {q.subtitle && <div style={S.qSub}>{q.subtitle}</div>}
      <div style={S.opts}>{(q.options || []).map((o, i) => (
        <div key={i} style={{ ...S.opt, ...(sel.includes(o) ? S.optSel : {}) }} onClick={() => toggle(o)}>
          <div style={{ ...S.chk, ...(sel.includes(o) ? S.chkSel : {}) }}>{sel.includes(o) && '✓'}</div><span>{o}</span>
        </div>
      ))}</div>
    </>
  );
}

function OpenQ({ q, a, onA }) {
  return (
    <>
      <div style={S.qTitle}>{q.title}</div>
      <textarea style={S.ta} placeholder={q.placeholder || ''} value={a || ''} onChange={e => onA(e.target.value)} rows={4} />
      <div style={S.taCount}>{(a || '').length} 字</div>
    </>
  );
}

function AnchorQ({ q, a, onA, tasks }) {
  const cur = a || {};
  return (
    <>
      <div style={S.qTitle}>{q.title}</div>
      {q.subtitle && <div style={S.qSub}>{q.subtitle}</div>}
      <div style={S.opts}>{(tasks || []).map(t => (
        <div key={t.id} style={{ ...S.opt, ...(cur.taskId === t.id ? S.optSel : {}) }}
          onClick={() => onA({ ...cur, taskId: t.id, dishName: t.dish_name })}>
          <div style={{ ...S.radio, ...(cur.taskId === t.id ? S.radioSel : {}) }}>{cur.taskId === t.id && <div style={S.radioDot} />}</div>
          <div>
            <div style={{ fontWeight: 600 }}>{t.dish_name} <span style={{ fontWeight: 400, color: '#94a3b8', fontSize: 12 }}>#{t.recipe_id} · {typeLabel(t.recipe_type)}</span></div>
            <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 2 }}>{t.customer_name} · ×{t.exec_count} · {t.status === 'failed' ? '失败' : '通过'}</div>
          </div>
        </div>
      ))}</div>
      {cur.taskId && <>
        <div style={{ ...S.qSub, marginTop: 12 }}>补充原因（选填）</div>
        <textarea style={{ ...S.ta, marginTop: 4 }} placeholder={q.placeholder || '为什么选这道菜？'} value={cur.reason || ''}
          onChange={e => onA({ ...cur, reason: e.target.value })} rows={2} />
      </>}
    </>
  );
}

// ============================================================
// SHARED
// ============================================================
function StatBox({ n, label, color }) {
  return (
    <div style={S.statBox}>
      <div style={{ ...S.statN, color: color || '#1e293b' }}>{n}</div>
      <div style={S.statL}>{label}</div>
    </div>
  );
}

// ============================================================
// STYLES
// ============================================================
const S = {
  root: { minHeight: '100vh', background: '#f0f2f5', display: 'flex', justifyContent: 'center', padding: '12px 0' },
  shell: { width: '100%', maxWidth: 480, background: '#fff', borderRadius: 16, overflow: 'hidden', boxShadow: '0 4px 24px rgba(0,0,0,0.08)', minHeight: '90vh', display: 'flex', flexDirection: 'column' },
  content: { padding: '14px 18px', flex: 1 },

  // Admin header
  adminHeader: { padding: '16px 18px', borderBottom: '1px solid #f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'space-between' },
  logoBox: { width: 36, height: 36, borderRadius: 10, background: '#1e3a5f', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 700 },

  // Tabs
  tabBar: { display: 'flex', borderBottom: '1px solid #f1f5f9', padding: '0 18px' },
  tabItem: { padding: '10px 14px', fontSize: 13, fontWeight: 500, color: '#94a3b8', cursor: 'pointer', borderBottom: '2px solid transparent', marginBottom: -1 },
  tabItemActive: { color: '#1e293b', borderBottomColor: '#2563eb' },

  // Date / sync
  dateInput: { padding: '6px 10px', border: '1px solid #e2e8f0', borderRadius: 8, fontSize: 13, color: '#475569', fontFamily: 'inherit' },
  syncBtnSm: { padding: '6px 14px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: 8, fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit', whiteSpace: 'nowrap' },
  exportBtn: { padding: '6px 14px', background: '#f8fafc', color: '#475569', border: '1px solid #e2e8f0', borderRadius: 8, fontSize: 12, fontWeight: 500, cursor: 'pointer', fontFamily: 'inherit', whiteSpace: 'nowrap' },

  // Stats
  statsRow: { display: 'flex', gap: 8, marginBottom: 14 },
  statBox: { flex: 1, textAlign: 'center', background: '#f8fafc', borderRadius: 10, padding: '10px 4px' },
  statN: { fontSize: 20, fontWeight: 700, color: '#1e293b' },
  statL: { fontSize: 11, color: '#94a3b8', marginTop: 2 },

  // Section
  secHead: { fontSize: 13, fontWeight: 600, color: '#475569', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 },
  countBadge: { background: '#eff6ff', color: '#2563eb', fontSize: 11, fontWeight: 600, padding: '2px 8px', borderRadius: 10 },
  empty: { textAlign: 'center', padding: 40, color: '#94a3b8', fontSize: 14 },

  // Engineer rows
  engRow: { display: 'flex', alignItems: 'center', gap: 10, padding: '10px 0', borderBottom: '1px solid #f8fafc', cursor: 'pointer' },
  dot: { width: 8, height: 8, borderRadius: 4, flexShrink: 0 },

  // Detail expand
  detailBox: { padding: '14px 16px', background: '#f8fafc', borderRadius: 10, margin: '4px 0 10px', border: '1px solid #f1f5f9' },
  trigBadge: { display: 'inline-block', background: '#fef3c7', color: '#b45309', fontSize: 10, fontWeight: 600, padding: '1px 6px', borderRadius: 4 },

  // Candidates
  candidateCard: { border: '1px solid #e2e8f0', borderRadius: 10, padding: 14, marginBottom: 8 },
  catBadge: { fontSize: 11, fontWeight: 600, padding: '2px 8px', borderRadius: 6, background: '#f8fafc' },
  filterBtn: { padding: '5px 12px', border: '1px solid #e2e8f0', borderRadius: 8, fontSize: 12, fontWeight: 500, color: '#64748b', background: '#fff', cursor: 'pointer', fontFamily: 'inherit' },
  filterBtnActive: { background: '#1e293b', color: '#fff', borderColor: '#1e293b' },
  miniBtn: { padding: '4px 10px', border: '1px solid #e2e8f0', borderRadius: 6, fontSize: 12, fontWeight: 500, color: '#475569', background: '#fff', cursor: 'pointer', fontFamily: 'inherit' },

  // Questions management
  qRow: { display: 'flex', alignItems: 'flex-start', gap: 12, padding: '12px 0', borderBottom: '1px solid #f8fafc' },
  qKey: { fontSize: 11, fontWeight: 700, color: '#2563eb', background: '#eff6ff', padding: '1px 6px', borderRadius: 4, fontFamily: 'monospace' },
  qType: { fontSize: 11, fontWeight: 500, color: '#64748b', background: '#f1f5f9', padding: '1px 6px', borderRadius: 4 },
  addBtn: { padding: '6px 14px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: 8, fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit' },

  // Form
  formBox: { padding: 16, background: '#f8fafc', borderRadius: 10, border: '1px solid #e2e8f0', marginBottom: 12 },
  formRow: { marginBottom: 10 },
  formLabel: { fontSize: 12, fontWeight: 600, color: '#475569', display: 'block', marginBottom: 4 },
  formInput: { width: '100%', padding: '8px 10px', border: '1px solid #e2e8f0', borderRadius: 8, fontSize: 13, color: '#1e293b', fontFamily: 'inherit', boxSizing: 'border-box' },
  saveBtnPri: { padding: '8px 20px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit' },
  saveBtnSec: { padding: '8px 20px', background: '#f1f5f9', color: '#475569', border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 500, cursor: 'pointer', fontFamily: 'inherit' },

  // Fill view
  fillHeader: { padding: '12px 16px', borderBottom: '1px solid #f1f5f9', textAlign: 'center' },
  body: { flex: 1, padding: '16px 14px 100px', overflowY: 'auto' },
  bubble: { display: 'flex', gap: 10, alignItems: 'flex-start' },
  botAv: { width: 36, height: 36, borderRadius: 10, background: '#1e3a5f', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, fontWeight: 700, flexShrink: 0 },
  bottom: { position: 'sticky', bottom: 0, background: '#fff', borderTop: '1px solid #f1f5f9', padding: '12px 20px 16px' },
  stepLabel: { fontSize: 12, color: '#94a3b8', fontWeight: 500, display: 'flex', alignItems: 'center', marginBottom: 8 },
  btns: { display: 'flex', gap: 8 },
  btnPri: { flex: 1, padding: '12px 20px', background: 'linear-gradient(135deg,#2563eb,#3b82f6)', color: '#fff', border: 'none', borderRadius: 10, fontSize: 14, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit' },
  btnSec: { padding: '12px 20px', background: '#f1f5f9', color: '#475569', border: 'none', borderRadius: 10, fontSize: 14, fontWeight: 500, cursor: 'pointer', fontFamily: 'inherit' },
  btnGreen: { flex: 1, padding: '12px 20px', background: 'linear-gradient(135deg,#059669,#10b981)', color: '#fff', border: 'none', borderRadius: 10, fontSize: 14, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit' },
  progOuter: { height: 3, background: '#f1f5f9' },
  progInner: { height: '100%', background: 'linear-gradient(90deg,#3b82f6,#2563eb)', borderRadius: 2, transition: 'width 0.4s ease' },
  successCircle: { width: 64, height: 64, borderRadius: 32, background: '#22c55e', color: '#fff', fontSize: 28, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' },

  // Cards
  card: { background: '#fff', border: '1px solid #e2e8f0', borderRadius: 14, padding: 16, boxShadow: '0 1px 4px rgba(0,0,0,0.04)' },
  cardHead: { marginBottom: 12, paddingBottom: 10, borderBottom: '1px solid #f1f5f9' },
  cardTitle: { fontSize: 15, fontWeight: 600, color: '#1e293b' },
  cardSub: { fontSize: 12, color: '#94a3b8', marginTop: 2 },
  taskCard: { background: '#fafbfc', border: '1px solid #f1f5f9', borderRadius: 10, padding: 12, marginBottom: 10 },
  taskHead: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', cursor: 'pointer', marginBottom: 6 },
  taskName: { fontSize: 14, fontWeight: 600, color: '#1e293b' },
  taskMeta: { fontSize: 11, color: '#94a3b8', marginTop: 2, fontFamily: 'monospace' },
  statusBadge: { fontSize: 11, fontWeight: 600, padding: '2px 8px', borderRadius: 6 },
  execBadge: { fontSize: 11, fontWeight: 500, padding: '2px 8px', borderRadius: 6, background: '#f8fafc', color: '#64748b' },
  ctxRow: { display: 'flex', gap: 6, fontSize: 11, color: '#94a3b8', marginBottom: 8, flexWrap: 'wrap' },
  ctxItem: { background: '#f1f5f9', padding: '1px 6px', borderRadius: 4 },
  sec: { marginTop: 8 },
  secTitle: { fontSize: 11, fontWeight: 600, color: '#475569', marginBottom: 4, letterSpacing: 0.5 },
  powerRow: { display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 2 },
  expandBtn: { textAlign: 'center', fontSize: 11, color: '#3b82f6', cursor: 'pointer', padding: '6px 0 2px', fontWeight: 500 },
  abnormal: { marginTop: 8, padding: '8px 10px', background: '#fef2f2', borderRadius: 8, fontSize: 11, color: '#dc2626', fontWeight: 500, lineHeight: 1.5 },
  footNote: { marginTop: 12, padding: '10px 12px', background: '#eff6ff', borderRadius: 10, fontSize: 12, color: '#3b82f6', lineHeight: 1.5, fontWeight: 500 },

  // Questions (fill)
  qTitle: { fontSize: 15, fontWeight: 600, color: '#1e293b', lineHeight: 1.5, marginBottom: 4 },
  qSub: { fontSize: 12, color: '#94a3b8', marginBottom: 8 },
  opts: { display: 'flex', flexDirection: 'column', gap: 6, marginTop: 8 },
  opt: { display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', borderRadius: 10, border: '1px solid #e2e8f0', cursor: 'pointer', fontSize: 13, color: '#475569', transition: 'all .15s', lineHeight: 1.4 },
  optSel: { background: '#eff6ff', borderColor: '#93c5fd', color: '#1e40af', fontWeight: 500 },
  radio: { width: 18, height: 18, borderRadius: 9, border: '2px solid #cbd5e1', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 },
  radioSel: { borderColor: '#2563eb' },
  radioDot: { width: 8, height: 8, borderRadius: 4, background: '#2563eb' },
  chk: { width: 18, height: 18, borderRadius: 5, border: '2px solid #cbd5e1', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, color: '#fff', fontSize: 11, fontWeight: 700 },
  chkSel: { background: '#2563eb', borderColor: '#2563eb' },
  ta: { width: '100%', padding: '12px 14px', border: '1px solid #e2e8f0', borderRadius: 10, fontSize: 14, color: '#1e293b', lineHeight: 1.6, resize: 'vertical', outline: 'none', fontFamily: 'inherit', boxSizing: 'border-box' },
  taCount: { textAlign: 'right', fontSize: 11, color: '#cbd5e1', marginTop: 4 },
  trigContextBanner: { padding: '10px 14px', background: '#fffbeb', border: '1px solid #fde68a', borderRadius: 10, marginBottom: 14 },
};
