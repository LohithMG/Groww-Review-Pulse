import { useState } from 'react';
import { Settings, BarChart3, Mail, RefreshCw, Send, CheckCircle2, Clock, Star, MessageSquare } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

function App() {
  const [weeks, setWeeks] = useState(8);
  const [maxReviews, setMaxReviews] = useState(500);
  const [isLoading, setIsLoading] = useState(false);
  const [pulseData, setPulseData] = useState(null);
  
  // Email state
  const [emailRecipient, setEmailRecipient] = useState('');
  const [isEmailing, setIsEmailing] = useState(false);
  const [emailStatus, setEmailStatus] = useState(null);

  const handleAnalyze = async () => {
    setIsLoading(true);
    setPulseData(null);
    setEmailStatus(null);
    try {
      const response = await fetch('http://localhost:8000/api/v1/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          weeks: weeks,
          max_reviews: maxReviews,
        }),
      });
      
      const result = await response.json();
      if (response.ok && result.status === 'success') {
        setPulseData(result.data);
      } else {
        alert(`Analysis failed: ${result.detail || 'Unknown error'}`);
      }
    } catch (error) {
      alert(`API Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendEmail = async (e) => {
    e.preventDefault();
    if (!emailRecipient || !emailRecipient.includes('@')) {
      alert("Please enter a valid email address");
      return;
    }

    setIsEmailing(true);
    setEmailStatus(null);

    try {
      const response = await fetch('http://localhost:8000/api/v1/email', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          recipient_email: emailRecipient,
          pulse_data: pulseData,
        }),
      });
      
      const result = await response.json();
      if (response.ok) {
        setEmailStatus({ success: true, message: result.message });
      } else {
        setEmailStatus({ success: false, message: result.detail || 'Failed to send' });
      }
    } catch (error) {
      setEmailStatus({ success: false, message: `API Error: ${error.message}` });
    } finally {
      setIsEmailing(false);
    }
  };

  return (
    <div className="flex min-h-screen relative overflow-hidden bg-[#0b0e14]">
      {/* ── Animated Background Mesh ── */}
      <div className="absolute inset-0 z-0 pointer-events-none w-full h-full overflow-hidden">
        {/* Top Left Blob */}
        <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-emerald-900/30 rounded-full mix-blend-screen mix-blend-screen filter blur-[100px] opacity-70 animate-blob"></div>
        
        {/* Top Right Blob */}
        <div className="absolute top-[0%] right-[-5%] w-[600px] h-[600px] bg-teal-900/40 rounded-full mix-blend-screen filter blur-[120px] opacity-60 animate-blob animation-delay-2000"></div>
        
        {/* Bottom Left Blob */}
        <div className="absolute bottom-[-20%] left-[20%] w-[700px] h-[700px] bg-slate-800/50 rounded-full mix-blend-screen filter blur-[130px] opacity-50 animate-blob animation-delay-4000"></div>

        {/* Center Accent Blob */}
        <div className="absolute top-[40%] left-[40%] w-[400px] h-[400px] bg-emerald-700/20 rounded-full mix-blend-screen filter blur-[100px] opacity-40 animate-blob"></div>
      </div>

      {/* ── Sidebar ── */}
      <div className="w-80 bg-[#12151c]/60 backdrop-blur-2xl border-r border-white/5 p-6 flex flex-col min-h-screen sticky top-0 z-10">
        <div className="flex items-center gap-3 mb-8 pb-8 border-b border-white/5">
          <Settings className="text-emerald-400 w-6 h-6" />
          <h2 className="text-2xl m-0">Filter</h2>
        </div>

        <div className="space-y-6">
          <div>
            <div className="flex justify-between text-sm mb-2">
              <label className="text-slate-300 font-medium">Weeks to analyse</label>
              <span className="text-emerald-400 font-bold">{weeks}</span>
            </div>
            <input 
              type="range" min="4" max="12" value={weeks} 
              onChange={(e) => setWeeks(Number(e.target.value))}
              className="w-full accent-emerald-500"
            />
          </div>

          <div>
            <div className="flex justify-between text-sm mb-2">
              <label className="text-slate-300 font-medium">Max reviews to fetch</label>
              <span className="text-emerald-400 font-bold">{maxReviews}</span>
            </div>
            <input 
              type="range" min="100" max="5000" step="100" value={maxReviews} 
              onChange={(e) => setMaxReviews(Number(e.target.value))}
              className="w-full accent-emerald-500"
            />
          </div>
        </div>

        <div className="mt-auto pt-6 border-t border-white/5 text-xs text-slate-500 flex items-center gap-2">
          <span>📦 Built by Lohith</span>
        </div>
      </div>

      {/* ── Main Content ── */}
      <div className="flex-1 p-10 max-w-5xl z-10 relative">
        
        {/* Header */}
        <div className="mb-10 pb-6 border-b border-white/5">
          <div className="flex items-center gap-4 mb-2">
            <BarChart3 className="text-emerald-400 w-10 h-10" />
            <h1 className="text-4xl m-0 mt-1">Groww Review Pulse Engine</h1>
          </div>
          <p className="text-slate-400">
            Turn Play Store reviews into a weekly PM insight note · Fetching up to {maxReviews} reviews from last {weeks} weeks
          </p>
        </div>

        {/* Trigger Button */}
        {!pulseData && (
          <button 
            onClick={handleAnalyze} 
            disabled={isLoading}
            className="btn-primary w-full md:w-auto flex items-center justify-center gap-3 text-lg py-4 px-8 mb-12"
          >
            {isLoading ? <RefreshCw className="animate-spin" /> : <Send />}
            {isLoading ? "Analyzing via Map-Reduce Pipeline..." : "🚀 Analyze Latest Reviews"}
          </button>
        )}

        {/* ── Pulse Dashboard ── */}
        {pulseData && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
            
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-2xl m-0 flex items-center gap-2">
                <CheckCircle2 className="w-6 h-6 text-emerald-400" /> 
                Weekly Pulse Preview
              </h2>
              <button 
                onClick={handleAnalyze} 
                className="text-emerald-400 hover:text-emerald-300 text-sm flex items-center gap-2 transition-colors"
              >
                <RefreshCw className="w-4 h-4" /> Run Again
              </button>
            </div>

            {/* Weekly Trend Graph */}
            {pulseData.trend_data && pulseData.trend_data.length > 0 && (
              <div className="glass-card mb-10 w-full h-80 pt-6">
                <h3 className="text-xl mb-4 font-sans text-slate-100 px-6">
                  Weekly Average Rating
                </h3>
                <ResponsiveContainer width="100%" height="80%">
                  <LineChart data={pulseData.trend_data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                    <XAxis 
                      dataKey="weekLabel" 
                      stroke="#64748b" 
                      fontSize={12} 
                      tickLine={false}
                      axisLine={false}
                    />
                    <YAxis 
                      domain={[1, 5]} 
                      stroke="#64748b" 
                      fontSize={12}
                      tickLine={false}
                      axisLine={false}
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'rgba(26, 29, 39, 0.9)', 
                        borderColor: 'rgba(255,255,255,0.1)',
                        borderRadius: '8px',
                        backdropFilter: 'blur(10px)'
                      }}
                      itemStyle={{ color: '#00d09c' }}
                      formatter={(value, name, props) => [
                        `${value}★ (${props.payload.count} reviews)`, 
                        'Average Rating'
                      ]}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="avgRating" 
                      stroke="#00d09c" 
                      strokeWidth={3}
                      dot={{ fill: '#0b0e14', stroke: '#00d09c', strokeWidth: 2, r: 4 }}
                      activeDot={{ r: 6, fill: '#00d09c', stroke: '#fff', strokeWidth: 2 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Metrics Row */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
              <div className="glass-card mb-0 flex flex-col">
                <span className="text-slate-400 text-sm mb-1">Reviews</span>
                <span className="text-3xl font-bold flex items-center gap-2">
                  <MessageSquare className="w-6 h-6 text-emerald-500/50" />
                  {pulseData.total_reviews}
                </span>
              </div>
              <div className="glass-card mb-0 flex flex-col">
                <span className="text-slate-400 text-sm mb-1">Avg Rating</span>
                <span className="text-3xl font-bold flex items-center gap-2">
                  <Star className="w-6 h-6 text-emerald-500/50" />
                  {pulseData.avg_rating}
                </span>
              </div>
              <div className="glass-card mb-0 flex flex-col justify-center">
                <span className="text-slate-400 text-sm mb-1">Period</span>
                <span className="text-sm md:text-xs lg:text-sm xl:text-base font-bold flex items-start gap-2 mt-1 leading-tight">
                  <Clock className="w-4 h-4 text-emerald-500/50 shrink-0 mt-[2px]" />
                  <span>{pulseData.date_range}</span>
                </span>
              </div>
              <div className="glass-card mb-0 flex flex-col">
                <span className="text-slate-400 text-sm mb-1">Sentiment</span>
                <span className="text-2xl font-bold capitalize text-amber-400">
                  {pulseData.overall_sentiment}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-10">
              {/* Left Column: Themes & Actions */}
              <div>
                <h3 className="text-xl mb-4 font-sans flex items-center gap-2 text-slate-100">
                  <span className="text-2xl">🏷️</span> Top 3 Themes
                </h3>
                {pulseData.top_3_themes?.map((t, idx) => (
                  <div key={idx} className="theme-card">
                    <div className="flex items-center justify-between mb-2">
                      <strong className="text-lg">{t.rank}. {t.name}</strong>
                      <span className="text-xl">
                        {t.sentiment === 'negative' ? '🔴' : t.sentiment === 'positive' ? '🟢' : '🟡'}
                      </span>
                    </div>
                    <div className="text-sm text-slate-400 mb-2">
                      {t.review_count} mentions · {t.sentiment}
                    </div>
                    <p className="text-slate-300 m-0">{t.summary}</p>
                  </div>
                ))}

                <h3 className="text-xl mb-4 mt-8 font-sans flex items-center gap-2 text-slate-100">
                  <span className="text-2xl">⚡</span> 3 Action Ideas
                </h3>
                {pulseData.top_3_actions?.map((action, idx) => (
                  <div key={idx} className="action-card">
                    <strong>{idx + 1}.</strong> {action}
                  </div>
                ))}
              </div>

              {/* Right Column: Quotes */}
              <div>
                <h3 className="text-xl mb-4 font-sans flex items-center gap-2 text-slate-100">
                  <span className="text-2xl">💬</span> User Voices
                </h3>
                {pulseData.top_3_quotes?.map((quote, idx) => (
                  <div key={idx} className="quote-card">
                    "{quote}"
                  </div>
                ))}
              </div>
            </div>

            {/* Email Section */}
            <div className="glass-card bg-slate-900/40 p-8 border-emerald-500/20">
              <h3 className="text-xl mb-4 font-sans flex items-center gap-2 text-slate-100">
                <Mail className="text-emerald-400" /> Send Pulse Report
              </h3>
              
              <form onSubmit={handleSendEmail} className="flex flex-col gap-4 max-w-md">
                <input 
                  type="email" 
                  required
                  placeholder="recipient@gmail.com"
                  className="bg-[#0f1117] border border-white/10 rounded-lg px-4 py-3 text-slate-200 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all"
                  value={emailRecipient}
                  onChange={(e) => setEmailRecipient(e.target.value)}
                />
                
                <button 
                  type="submit" 
                  disabled={isEmailing}
                  className="btn-primary flex items-center justify-center gap-2"
                >
                  {isEmailing ? <RefreshCw className="animate-spin w-4 h-4" /> : <Send className="w-4 h-4" />}
                  {isEmailing ? "Sending Pulse via SMTP..." : "Send Email Now"}
                </button>
              </form>

              {emailStatus && (
                <div className={`mt-4 p-4 rounded-lg flex items-center gap-3 ${emailStatus.success ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'}`}>
                   {emailStatus.success ? <CheckCircle2 className="w-5 h-5 shrink-0" /> : <span className="text-xl">❌</span>}
                   {emailStatus.message}
                </div>
              )}
            </div>

          </div>
        )}

      </div>
    </div>
  );
}

export default App;
