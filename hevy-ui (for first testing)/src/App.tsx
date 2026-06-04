import { useState, useEffect, useRef, type ReactNode, type HTMLAttributes } from 'react';

interface Message {
  id: number;
  sender: 'ai' | 'user';
  text: string;
  type: 'text';
}

type IconProps = HTMLAttributes<HTMLSpanElement> & { children?: ReactNode; size?: number | string };

const Icon = ({ children, className, size, ...props }: IconProps) => (
  <span className={`inline-flex ${className ?? ''}`} {...props}>
    {children}
  </span>
);

const Activity = (props: IconProps) => <Icon {...props}>📊</Icon>;
const Dumbbell = (props: IconProps) => <Icon {...props}>🏋️</Icon>;
const Calendar = (props: IconProps) => <Icon {...props}>📅</Icon>;
const User = (props: IconProps) => <Icon {...props}>👤</Icon>;
const Bot = (props: IconProps) => <Icon {...props}>🤖</Icon>;
const Send = (props: IconProps) => <Icon {...props}>➡️</Icon>;
const RefreshCcw = (props: IconProps) => <Icon {...props}>🔄</Icon>;
const Sparkles = (props: IconProps) => <Icon {...props}>✨</Icon>;
const ChevronRight = (props: IconProps) => <Icon {...props}>›</Icon>;
const MessageSquare = (props: IconProps) => <Icon {...props}>💬</Icon>;
const Plus = (props: IconProps) => <Icon {...props}>＋</Icon>;
const Settings = (props: IconProps) => <Icon {...props}>⚙️</Icon>;
const Info = (props: IconProps) => <Icon {...props}>ℹ️</Icon>;
const ChevronDown = (props: IconProps) => <Icon {...props}>⌄</Icon>;
const ThumbsUp = (props: IconProps) => <Icon {...props}>👍</Icon>;
const Folder = (props: IconProps) => <Icon {...props}>📁</Icon>;
const Sliders = (props: IconProps) => <Icon {...props}>🎚️</Icon>;
const ChevronLeft = (props: IconProps) => <Icon {...props}>‹</Icon>;

// Dữ liệu phân tích mẫu từ AI dựa trên lịch sử tập để phản hồi tự nhiên cho người dùng
const COACH_KNOWLEDGE = {
  bench: "📊 **Phân tích tiến trình bài Incline Bench Press (Dumbbell):**\n\nChúc mừng bạn! Trong **4 tuần qua**, bạn đã có sự tiến bộ rất rõ rệt:\n* **Khối lượng tối đa (Estimated 1RM):** Tăng từ **22.5kg** lên **25kg** (+11.1%).\n* **Volume buổi gần nhất (25/5):** Đạt **180kg** tổng lượng tạ nâng.\n\n🔥 **Gợi ý Overload:** Buổi tập ngực tới (thứ Tư), bạn hoàn toàn có thể thử sức tăng tạ lên **25kg ở Set 1** (mục tiêu 6 reps) vì dữ liệu cho thấy nhịp tim hồi phục của bạn đang rất tốt.",
  general: "🤔 **Tôi cần thêm một chút thông tin từ chickenlegg:**\n\nLịch sử tập luyện của bạn trong 1 tháng qua rất đều đặn (3-5 buổi/tuần). Tuy nhiên, để nhận xét chính xác bạn có đang 'tập tốt' hay không, bạn muốn tôi đánh giá khía cạnh nào cụ thể hơn?\n\n1. **Tiến trình của một bài tập cụ thể** (Ví dụ: *Incline Bench Press* hay *Pendlay Row*?)\n2. **Sự cân bằng nhóm cơ** (Phát triển đều ngực/lưng/tay?)\n3. **Mục tiêu tăng cơ hay giảm mỡ?**\n\nBạn có thể nhấn chọn một bài tập bất kỳ bên danh sách Dashboard hoặc gõ tên bài tập ở dưới đây nhé!",
  missing: "🔍 **Không tìm thấy dữ liệu tập Squat:**\n\nTôi đã quét toàn bộ lịch sử tập 3 tháng qua của tài khoản **chickenlegg** nhưng không thấy dữ liệu ghi chép (log) cho bài tập **Squat (Gánh đùi sau/trước)**.\n\n* **Lý do:** Bạn chưa từng lưu bài tập này trong các routine đã hoàn thành trên Hevy.\n* **Khắc phục:** Hãy thử log bài tập Squat vào buổi tập thân dưới tới, hoặc bạn có muốn tôi phân tích các bài tập đùi/mông khác có sẵn trong lịch sử của bạn không?",
  sick: "✍ *Đã ghi nhận ngữ cảnh mới:*\n\nÀ, tôi hiểu rồi! Cảm ơn bạn đã đính chính. Thời gian nghỉ ốm 10 ngày giải thích lý do tại sao Volume tập của tuần cuối tháng 4 bị giảm đột ngột xuống mức thấp nhất trên biểu đồ.\n\n🔄 **Đánh giá lại xu hướng sau hồi phục:**\n* Nếu bỏ qua giai đoạn nghỉ bệnh, tốc độ lấy lại thể lực của bạn thực tế rất nhanh. Chỉ sau 2 buổi tập lại, mức tạ Incline Bench Press của bạn đã quay lại mốc **22.5kg x 8 reps**.\n* **Lời khuyên:** Đừng vội tăng tạ ngay tuần này. Hãy duy trì mức tạ hiện tại thêm 1 buổi nữa để cơ gân khớp thích nghi hoàn toàn sau đợt ốm nhé!"
};

// Cấu trúc dữ liệu chi tiết cho 3 giáo án tập để chuyển đổi động
const ROUTINES_DATA = {
  "upper 2": {
    name: "upper 2",
    volume: "4218 kg",
    date: "May 21",
    chartPath: "M 10,60 L 90,110 L 170,40 L 250,130 L 330,90 L 410,20 L 490,110",
    chartPoints: [
      { cx: 10, cy: 60 }, { cx: 90, cy: 110 }, { cx: 170, cy: 40 }, 
      { cx: 250, cy: 130 }, { cx: 330, cy: 90 }, { cx: 410, cy: 20, isPeak: true }, { cx: 490, cy: 110 }
    ],
    exercises: [
      {
        abbr: "BP",
        name: "Incline Bench Press (Dumbbell)",
        category: "Chest",
        sets: [
          { num: 1, weight: "22.5 kg", reps: "8 reps" },
          { num: 2, weight: "22.5 kg", reps: "5 reps" }
        ]
      },
      {
        abbr: "LP",
        name: "Single Arm Lat Pulldown",
        category: "Back",
        sets: [
          { num: 1, weight: "40 kg", reps: "12 reps" },
          { num: 2, weight: "40 kg", reps: "10 reps" }
        ]
      }
    ]
  },
  "leg mtfk, leg": {
    name: "leg mtfk, leg",
    volume: "3850 kg",
    date: "May 18",
    chartPath: "M 10,120 L 90,80 L 170,95 L 250,30 L 330,70 L 410,110 L 490,50",
    chartPoints: [
      { cx: 10, cy: 120 }, { cx: 90, cy: 80 }, { cx: 170, cy: 95 }, 
      { cx: 250, cy: 30, isPeak: true }, { cx: 330, cy: 70 }, { cx: 410, cy: 110 }, { cx: 490, cy: 50 }
    ],
    exercises: [
      {
        abbr: "SQ",
        name: "Squat (Barbell)",
        category: "Legs",
        sets: [
          { num: 1, weight: "80 kg", reps: "8 reps" },
          { num: 2, weight: "80 kg", reps: "6 reps" }
        ]
      },
      {
        abbr: "RD",
        name: "Romanian Deadlift (Barbell)",
        category: "Legs / Glutes",
        sets: [
          { num: 1, weight: "70 kg", reps: "10 reps" },
          { num: 2, weight: "70 kg", reps: "8 reps" }
        ]
      }
    ]
  },
  "upper": {
    name: "upper",
    volume: "4325 kg",
    date: "May 25",
    chartPath: "M 10,90 L 90,50 L 170,110 L 250,40 L 330,120 L 410,40 L 490,25",
    chartPoints: [
      { cx: 10, cy: 90 }, { cx: 90, cy: 50 }, { cx: 170, cy: 110 }, 
      { cx: 250, cy: 40 }, { cx: 330, cy: 120 }, { cx: 410, cy: 40 }, { cx: 490, cy: 25, isPeak: true }
    ],
    exercises: [
      {
        abbr: "BP",
        name: "Incline Bench Press (Dumbbell)",
        category: "Chest",
        sets: [
          { num: 1, weight: "22.5 kg", reps: "8 reps" },
          { num: 2, weight: "22.5 kg", reps: "5 reps" }
        ]
      },
      {
        abbr: "BF",
        name: "Butterfly (Pec Deck)",
        category: "Chest",
        sets: [
          { num: 1, weight: "40 kg", reps: "9 reps" },
          { num: 2, weight: "40 kg", reps: "6 reps" }
        ]
      },
      {
        abbr: "PR",
        name: "Pendlay Row (Barbell)",
        category: "Back",
        sets: [
          { num: 1, weight: "50 kg", reps: "10 reps" },
          { num: 2, weight: "50 kg", reps: "8 reps" }
        ]
      }
    ]
  }
};

type RoutineName = keyof typeof ROUTINES_DATA;

const barHeightClasses: Record<string, string> = {
  '85%': 'h-[85%]',
  '65%': 'h-[65%]',
  '95%': 'h-[95%]',
  '75%': 'h-[75%]',
  '20%': 'h-[20%]',
  '90%': 'h-[90%]',
  '45%': 'h-[45%]',
};

const barWidthClasses: Record<string, string> = {
  '38%': 'w-[38%]',
  '36%': 'w-[36%]',
  '21%': 'w-[21%]',
};

export default function App() {
  const [currentTab, setCurrentTab] = useState<'profile' | 'workout-hub' | 'routine-detail' | 'workout-detail' | 'coach'>('profile');
  const [selectedExercise, setSelectedExercise] = useState<string | null>(null);
  const [selectedRoutine, setSelectedRoutine] = useState<RoutineName>('upper 2'); // Lưu trữ giáo án được chọn động
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      sender: 'ai',
      text: "👋 Xin chào **chickenlegg**! Tôi là AI Coach cá nhân của bạn trên Hevy.\n\nTôi đã đồng bộ toàn bộ lịch sử tập luyện **133 workouts** của bạn. Hãy chọn một bài tập từ Dashboard hoặc hỏi tôi bất cứ điều gì để nhận phân tích tiến độ thực tế (ví dụ: *'Bench press của tôi tiến bộ thế nào?'*).",
      type: 'text'
    }
  ]);

  const chatEndRef = useRef<HTMLDivElement | null>(null);

  // Cuộn mượt mà xuống tin nhắn mới nhất trong tab Coach
  useEffect(() => {
    if (currentTab === 'coach') {
      const timer = setTimeout(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [messages, isTyping, currentTab]);

  const handleSendMessage = (text: string) => {
    if (!text.trim()) return;

    const newUserMessage: Message = {
      id: Date.now(),
      sender: 'user',
      text: text,
      type: 'text'
    };

    setMessages(prev => [...prev, newUserMessage]);
    setInputText('');
    setIsTyping(true);

    setTimeout(() => {
      setIsTyping(false);
      const cleanText = text.toLowerCase();
      let reply = "Tôi đã nhận được câu hỏi. Hệ thống AI đang phân tích sâu dữ liệu lịch sử tập của bạn dựa trên 133 buổi tập đã qua.";
      
      if (cleanText.includes("bench") || cleanText.includes("ngực") || cleanText.includes("incline") || cleanText.includes("tiến bộ")) {
        reply = COACH_KNOWLEDGE.bench;
        setSelectedExercise("Incline Bench Press (Dumbbell)");
      } else if (cleanText.includes("squat") || cleanText.includes("chân") || cleanText.includes("gánh")) {
        reply = COACH_KNOWLEDGE.missing;
      } else if (cleanText.includes("tốt không") || cleanText.includes("hiệu quả")) {
        reply = COACH_KNOWLEDGE.general;
      } else if (cleanText.includes("ốm") || cleanText.includes("sụt") || cleanText.includes("bệnh") || cleanText.includes("nghỉ")) {
        reply = COACH_KNOWLEDGE.sick;
      }

      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        sender: 'ai',
        text: reply,
        type: 'text'
      }]);
    }, 1000);
  };

  const handleExerciseClick = (exName: string) => {
    setSelectedExercise(exName);
    setCurrentTab('coach');
    setIsTyping(true);
    setTimeout(() => {
      setIsTyping(false);
      setMessages(prev => [...prev, {
        id: Date.now(),
        sender: 'ai',
        text: `📊 **Phân tích nhanh bài ${exName}:**\n\nBạn đang duy trì bài tập này với form dáng ổn định qua các buổi. \n* **Mức tạ buổi gần nhất:** Đạt tối đa **${exName.includes('Row') ? '50 kg' : exName.includes('Bench') ? '22.5 kg' : '40 kg'}**.\n* **Khuyến nghị Overload:** Nhịp tim phục hồi của bạn đang ở trạng thái tối ưu (90 giây nghỉ). Bạn đã sẵn sàng nâng thêm mức tạ tiếp theo ở set đầu tiên của buổi tập tới chưa?`,
        type: 'text'
      }]);
    }, 800);
  };

  // Hàm chuyển hướng và cấu hình giáo án động
  const handleRoutineSelect = (routineName: RoutineName) => {
    setSelectedRoutine(routineName);
    setCurrentTab('routine-detail');
  };

  const activeRoutine = ROUTINES_DATA[selectedRoutine];

  return (
    <div className="flex h-screen bg-black text-[#f1f1f2] font-sans overflow-hidden">
      <style dangerouslySetInnerHTML={{__html: `
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
          height: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: #08080a;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #2c2c2e;
          border-radius: 9999px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #007aff;
        }
        .delay-0 {
          animation-delay: 0ms;
        }
        .delay-150 {
          animation-delay: 150ms;
        }
        .delay-300 {
          animation-delay: 300ms;
        }
      `}} />
      
      {/* ========================================== */}
      {/* SIDEBAR NAVIGATION                         */}
      {/* ========================================== */}
      <aside className="w-80 bg-[#121212] border-r border-[#2c2c2e] flex flex-col justify-between flex-shrink-0">
        
        <div>
          <div className="p-6 border-b border-[#2c2c2e] flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-lg bg-[#007aff] flex items-center justify-center font-black text-white text-xl">
                H
              </div>
              <div>
                <span className="font-extrabold text-lg tracking-wide text-white">Hevy</span>
                <span className="text-xs text-[#8e8e93] block -mt-1">Web Pro Dashboard</span>
              </div>
            </div>
            <span className="bg-[#ffd60a] text-black text-[10px] font-black px-2 py-0.5 rounded-full uppercase tracking-wider">
              PRO
            </span>
          </div>

          {/* Profile khớp ảnh chickenlegg */}
          <div className="p-4 mx-4 mt-4 bg-[#1c1c1e] rounded-xl border border-[#2c2c2e] flex items-center gap-3">
            <img 
              src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&h=150&q=80"
              alt="Avatar chickenlegg"
              className="w-11 h-11 rounded-full object-cover border-2 border-[#2c2c2e] bg-[#2c2c2e]"
              onError={(e) => { (e.target as HTMLImageElement).src = 'https://via.placeholder.com/150'; }}
            />
            <div>
              <div className="flex items-center gap-1.5">
                <h4 className="font-bold text-white text-sm">chickenlegg</h4>
                <span className="text-[10px] bg-[#ffd60a]/15 text-[#ffd60a] px-1.5 py-0.2 rounded font-bold border border-[#ffd60a]/20">PRO</span>
              </div>
              <p className="text-xs text-[#8e8e93]">Monday, May 25, 2026 - 5:00pm</p>
            </div>
          </div>

          {/* Menu Điều hướng */}
          <nav className="px-3 mt-6 space-y-1">
            <div className="text-[10px] font-bold text-[#8e8e93] px-3.5 mb-2 uppercase tracking-widest">Giao diện chính</div>
            
            <button
              onClick={() => setCurrentTab('profile')}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-xs font-bold transition-all ${
                currentTab === 'profile' 
                  ? 'bg-[#1c1c1e] text-[#007aff] border border-[#2c2c2e]' 
                  : 'text-gray-400 hover:bg-[#121212] hover:text-white'
              }`}
            >
              <User size={16} />
              <span>1. Trang Cá Nhân (Profile)</span>
            </button>

            <button
              onClick={() => setCurrentTab('workout-hub')}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-xs font-bold transition-all ${
                currentTab === 'workout-hub' 
                  ? 'bg-[#1c1c1e] text-[#007aff] border border-[#2c2c2e]' 
                  : 'text-gray-400 hover:bg-[#121212] hover:text-white'
              }`}
            >
              <Dumbbell size={16} />
              <span>2. Trung Tâm Tập Luyện (Hub)</span>
            </button>

            <button
              onClick={() => handleRoutineSelect('upper 2')}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-xs font-bold transition-all ${
                currentTab === 'routine-detail' 
                  ? 'bg-[#1c1c1e] text-[#007aff] border border-[#2c2c2e]' 
                  : 'text-gray-400 hover:bg-[#121212] hover:text-white'
              }`}
            >
              <Folder size={16} />
              <span>3. Chi Tiết Giáo Án ({activeRoutine.name})</span>
            </button>

            <button
              onClick={() => setCurrentTab('workout-detail')}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-xs font-bold transition-all ${
                currentTab === 'workout-detail' 
                  ? 'bg-[#1c1c1e] text-[#007aff] border border-[#2c2c2e]' 
                  : 'text-gray-400 hover:bg-[#121212] hover:text-white'
              }`}
            >
              <Activity size={16} />
              <span>4. Chi Tiết Buổi Tập (upper)</span>
            </button>

            <div className="pt-4 border-t border-[#2c2c2e] my-2"></div>
            <div className="text-[10px] font-bold text-[#8e8e93] px-3.5 mb-2 uppercase tracking-widest">Trợ lý trí tuệ</div>

            <button
              onClick={() => setCurrentTab('coach')}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-xs font-bold transition-all ${
                currentTab === 'coach' 
                  ? 'bg-[#007aff] text-white shadow-md' 
                  : 'text-[#007aff] bg-[#007aff]/10 hover:bg-[#007aff]/20'
              }`}
            >
              <div className="flex items-center gap-3">
                <Bot size={16} />
                <span>Hevy AI Coach</span>
              </div>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            </button>
          </nav>
        </div>

        <div className="p-4 border-t border-[#2c2c2e] text-center text-[10px] text-gray-500">
          <span>Hevy v2.94.0 • Web Pro</span>
        </div>
      </aside>

      {/* ========================================== */}
      {/* MAIN CONTENT AREA                          */}
      {/* ========================================== */}
      <main className="flex-1 bg-black overflow-hidden flex flex-col min-h-0">
        
        {/* ========================================================== */}
        {/* SCREEN 1: PROFILE PAGE (Giống hệt image_6be39e.jpg)         */}
        {/* ========================================================== */}
        {currentTab === 'profile' && (
          <div className="flex-1 overflow-y-auto min-h-0 w-full custom-scrollbar">
            <div className="p-8 max-w-4xl mx-auto w-full">
              
              {/* Header Profile */}
              <div className="flex items-center justify-between mb-6">
                <h1 className="text-2xl font-black text-white tracking-tight">chickenlegg</h1>
                <div className="flex gap-2">
                  <button aria-label="Open settings" className="p-2 rounded-lg bg-[#1c1c1e] text-white hover:bg-[#2c2c2e]"><Settings size={18} /></button>
                </div>
              </div>

              {/* Bio & Avatar */}
              <div className="flex items-center gap-5 mb-6">
                <img 
                  src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&h=150&q=80"
                  className="w-16 h-16 rounded-full object-cover border-2 border-[#2c2c2e]"
                  alt="chickenlegg avatar"
                />
                <div className="flex gap-6 text-center">
                  <div>
                    <div className="text-lg font-black text-white">133</div>
                    <div className="text-xs text-gray-400">Workouts</div>
                  </div>
                  <div>
                    <div className="text-lg font-black text-white">2</div>
                    <div className="text-xs text-gray-400">Followers</div>
                  </div>
                  <div>
                    <div className="text-lg font-black text-white">2</div>
                    <div className="text-xs text-gray-400">Following</div>
                  </div>
                </div>
              </div>

              {/* Your profile is 80% finished Alert */}
              <div className="bg-[#1c2c3e]/30 border border-[#1a3a5f] rounded-xl p-4 mb-6 flex justify-between items-center cursor-pointer hover:bg-[#1c2c3e]/50 transition-all">
                <span className="text-sm font-semibold text-sky-400">Your profile is 80% finished</span>
                <ChevronRight size={16} className="text-sky-400" />
              </div>

              {/* 0 hours this week bar chart */}
              <div className="bg-[#1c1c1e] rounded-xl border border-[#2c2c2e] p-5 mb-6">
                <div className="flex justify-between items-center mb-4">
                  <div>
                    <div className="text-xs text-gray-400 uppercase font-bold tracking-widest">Time spent training</div>
                    <div className="text-xl font-black text-white mt-1">0 hours <span className="text-xs font-normal text-gray-400">this week</span></div>
                  </div>
                  <span className="text-xs text-gray-400 font-semibold flex items-center gap-1">Last 3 months <ChevronDown size={14} /></span>
                </div>

                {/* Biểu đồ cột cực đẹp tái lập từ ảnh */}
                <div className="h-40 flex items-end justify-between gap-3 pb-2 mb-4">
                  {[
                    { label: 'Mar 16', h: '85%' },
                    { label: 'Mar 30', h: '65%' },
                    { label: 'Apr 13', h: '95%' },
                    { label: 'Apr 27', h: '75%' },
                    { label: 'May 11', h: '20%' }, // Tuần sụt giảm do nghỉ ốm
                    { label: 'May 25', h: '90%' },
                    { label: 'June 4', h: '45%' }
                  ].map((col, i) => (
                    <div key={i} className="flex-1 flex flex-col items-center group">
                      <div className={`w-full bg-[#0a84ff] rounded-t-sm transition-all group-hover:bg-[#30d158] ${barHeightClasses[col.h] ?? 'h-12'}`}></div>
                      <span className="text-[9px] text-gray-500 mt-2 whitespace-nowrap">{col.label}</span>
                    </div>
                  ))}
                </div>

                <div className="flex gap-2 text-xs">
                  <button className="bg-[#0a84ff] text-white px-4 py-1.5 rounded-full font-bold">Duration</button>
                  <button className="bg-[#2c2c2e] text-gray-400 hover:text-white px-4 py-1.5 rounded-full font-bold">Volume</button>
                  <button className="bg-[#2c2c2e] text-gray-400 hover:text-white px-4 py-1.5 rounded-full font-bold">Reps</button>
                </div>
              </div>

              {/* Dashboard Grid Buttons */}
              <div className="mb-6">
                <h3 className="text-sm font-black text-gray-400 uppercase tracking-widest mb-3">Dashboard</h3>
                <div className="grid grid-cols-2 gap-3">
                  <button className="p-4 bg-[#1c1c1e] border border-[#2c2c2e] rounded-xl flex items-center gap-3 hover:bg-[#2c2c2e] transition-all text-left">
                    <Activity size={18} className="text-[#0a84ff]" />
                    <span className="text-sm font-bold text-white">Statistics</span>
                  </button>
                  <button className="p-4 bg-[#1c1c1e] border border-[#2c2c2e] rounded-xl flex items-center gap-3 hover:bg-[#2c2c2e] transition-all text-left">
                    <Dumbbell size={18} className="text-[#0a84ff]" />
                    <span className="text-sm font-bold text-white">Exercises</span>
                  </button>
                  <button className="p-4 bg-[#1c1c1e] border border-[#2c2c2e] rounded-xl flex items-center gap-3 hover:bg-[#2c2c2e] transition-all text-left">
                    <Sliders size={18} className="text-[#0a84ff]" />
                    <span className="text-sm font-bold text-white">Measures</span>
                  </button>
                  <button className="p-4 bg-[#1c1c1e] border border-[#2c2c2e] rounded-xl flex items-center gap-3 hover:bg-[#2c2c2e] transition-all text-left">
                    <Calendar size={18} className="text-[#0a84ff]" />
                    <span className="text-sm font-bold text-white">Calendar</span>
                  </button>
                </div>
              </div>

              {/* Workouts History List (Bắt đầu với upper) */}
              <div>
                <h3 className="text-sm font-black text-gray-400 uppercase tracking-widest mb-3">Workouts</h3>
                <div 
                  onClick={() => setCurrentTab('workout-detail')}
                  className="p-4 bg-[#1c1c1e] border border-[#2c2c2e] rounded-xl cursor-pointer hover:border-[#0a84ff] transition-all"
                >
                  <div className="flex items-center gap-3 mb-3">
                    <img 
                      src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&h=150&q=80"
                      className="w-8 h-8 rounded-full object-cover"
                      alt="avatar"
                    />
                    <div>
                      <h4 className="text-sm font-bold text-white">chickenlegg</h4>
                      <p className="text-[10px] text-gray-500">Monday, May 25, 2026 - 5:00pm</p>
                    </div>
                  </div>
                  <h5 className="text-base font-black text-white">upper</h5>
                  <div className="flex gap-4 mt-2 text-xs text-gray-400">
                    <span>Time: <strong>1h 5min</strong></span>
                    <span>Volume: <strong>4.325 kg</strong></span>
                    <span>Sets: <strong>15</strong></span>
                  </div>
                </div>
              </div>

            </div>
          </div>
        )}

        {/* ========================================================== */}
        {/* SCREEN 2: WORKOUT HUB (Giống hệt image_6be366.jpg)          */}
        {/* ========================================================== */}
        {currentTab === 'workout-hub' && (
          <div className="flex-1 overflow-y-auto min-h-0 w-full custom-scrollbar">
            <div className="p-8 max-w-4xl mx-auto w-full">
              
              {/* Header */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2 cursor-pointer">
                  <h1 className="text-2xl font-black text-white">Workout</h1>
                  <ChevronDown size={20} className="text-[#007aff]" />
                </div>
                <span className="bg-[#ffd60a] text-black text-[10px] font-black px-2 py-0.5 rounded uppercase tracking-wider">
                  PRO
                </span>
              </div>

              {/* Nút Start Empty Workout */}
              <button className="w-full py-3 bg-[#1c1c1e] hover:bg-[#2c2c2e] border border-[#2c2c2e] rounded-xl text-sm font-bold text-[#0a84ff] flex items-center justify-center gap-2 mb-8 transition-all">
                <Plus size={16} />
                <span>Start Empty Workout</span>
              </button>

              {/* Khu vực Routines Header */}
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-sm font-black text-gray-400 uppercase tracking-widest">Routines</h3>
                <Folder size={18} className="text-[#0a84ff] cursor-pointer" />
              </div>

              {/* Nút New Routine & Explore */}
              <div className="grid grid-cols-2 gap-3 mb-8">
                <button className="p-4 bg-[#1c1c1e] border border-[#2c2c2e] rounded-xl text-center hover:bg-[#2c2c2e] transition-all">
                  <span className="text-sm font-bold text-white">New Routine</span>
                </button>
                <button className="p-4 bg-[#1c1c1e] border border-[#2c2c2e] rounded-xl text-center hover:bg-[#2c2c2e] transition-all">
                  <span className="text-sm font-bold text-white">Explore</span>
                </button>
              </div>

              {/* List Routines */}
              <div>
                <div className="flex items-center gap-1.5 mb-4 cursor-pointer text-gray-400 hover:text-white">
                  <ChevronDown size={14} />
                  <span className="text-xs font-bold uppercase tracking-widest">My Routines (4)</span>
                </div>

                <div className="space-y-3">
                  {/* Routine 1: upper 2 */}
                  <div 
                    onClick={() => handleRoutineSelect('upper 2')}
                    className="p-4 bg-[#1c1c1e] border border-[#2c2c2e] rounded-xl cursor-pointer hover:border-[#0a84ff] transition-all group"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="text-base font-black text-white group-hover:text-[#007aff] transition-colors">upper 2</h4>
                        <p className="text-xs text-gray-400 mt-1 line-clamp-1">Incline Bench Press (Dumbbell), Single Arm Lat Pulldown, Butterfly (Pec Deck), Chest Supported...</p>
                      </div>
                      <span className="text-[10px] text-gray-500">3 months ago</span>
                    </div>
                    <button 
                      onClick={(e) => {
                        e.stopPropagation(); // Ngăn sự kiện click của div cha
                        handleRoutineSelect('upper 2');
                      }}
                      className="mt-4 w-full py-2 bg-[#0a84ff] hover:bg-[#0062cc] text-white font-bold text-xs rounded-lg transition-all"
                    >
                      Start Routine
                    </button>
                  </div>

                  {/* Routine 2: leg mtfk, leg */}
                  <div 
                    onClick={() => handleRoutineSelect('leg mtfk, leg')}
                    className="p-4 bg-[#1c1c1e] border border-[#2c2c2e] rounded-xl cursor-pointer hover:border-[#0a84ff] transition-all group"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="text-base font-black text-white group-hover:text-[#007aff] transition-colors">leg mtfk, leg</h4>
                        <p className="text-xs text-gray-400 mt-1 line-clamp-1">Squat (Barbell), Romanian Deadlift (Barbell), Leg Extension (Machine), Shoulder Press (Dumbbell)...</p>
                      </div>
                    </div>
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRoutineSelect('leg mtfk, leg');
                      }}
                      className="mt-4 w-full py-2 bg-[#0a84ff] hover:bg-[#0062cc] text-white font-bold text-xs rounded-lg transition-all"
                    >
                      Start Routine
                    </button>
                  </div>

                  {/* Routine 3: upper */}
                  <div 
                    onClick={() => handleRoutineSelect('upper')}
                    className="p-4 bg-[#1c1c1e] border border-[#2c2c2e] rounded-xl cursor-pointer hover:border-[#0a84ff] transition-all group"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="text-base font-black text-white group-hover:text-[#007aff] transition-colors">upper</h4>
                        <p className="text-xs text-gray-400 mt-1 line-clamp-1">Incline Bench Press (Dumbbell), Pull Up (Weighted), Butterfly (Pec Deck), Pendlay Row...</p>
                      </div>
                    </div>
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRoutineSelect('upper');
                      }}
                      className="mt-4 w-full py-2 bg-[#0a84ff] hover:bg-[#0062cc] text-white font-bold text-xs rounded-lg transition-all"
                    >
                      Start Routine
                    </button>
                  </div>
                </div>

              </div>

            </div>
          </div>
        )}

        {/* ========================================================== */}
        {/* SCREEN 3: ROUTINE DETAIL "upper 2" / DYNAMIC (image_6be381) */}
        {/* ========================================================== */}
        {currentTab === 'routine-detail' && (
          <div className="flex-1 overflow-y-auto min-h-0 w-full custom-scrollbar">
            <div className="p-8 max-w-4xl mx-auto w-full">
              
              <button 
                onClick={() => setCurrentTab('workout-hub')}
                className="flex items-center gap-1.5 text-xs font-bold text-[#0a84ff] mb-6 hover:underline"
              >
                <ChevronLeft size={16} /> Quay lại Workout Hub
              </button>

              <div className="border-b border-[#2c2c2e] pb-6 mb-6">
                <div className="text-xs text-gray-500">Routine detail</div>
                <h1 className="text-2xl font-black text-white mt-1">{activeRoutine.name}</h1>
                <p className="text-xs text-gray-400 mt-1">Created by <span className="text-[#0a84ff] font-bold">chickenlegg</span></p>

                <button 
                  onClick={() => {
                    setCurrentTab('coach');
                    setIsTyping(true);
                    setTimeout(() => {
                      setIsTyping(false);
                      setMessages(prev => [...prev, {
                        id: Date.now(),
                        sender: 'ai',
                        text: `🚀 **Bạn vừa bắt đầu giáo án [${activeRoutine.name}]!** \n\n* **Tổng khối lượng dự kiến (Volume):** ${activeRoutine.volume}.\n* **Gợi ý từ Coach:** Hãy thực hiện khởi động kỹ khớp vai và khớp cổ tay trước khi bước vào set tập đầu tiên nhé. Bạn có muốn tôi xem biểu đồ Overload của các bài trong giáo án này không?`,
                        type: 'text'
                      }]);
                    }, 800);
                  }}
                  className="mt-4 w-full py-3 bg-[#0a84ff] hover:bg-[#0062cc] text-white font-black text-sm rounded-xl transition-all"
                >
                  Start Routine (Bắt đầu buổi tập)
                </button>
              </div>

              {/* Biểu đồ Volume dập dềnh của Routine khớp image_6be381.jpg */}
              <div className="bg-[#1c1c1e] border border-[#2c2c2e] rounded-xl p-5 mb-6">
                <div className="flex justify-between items-center mb-4">
                  <div>
                    <h3 className="text-base font-black text-white">{activeRoutine.volume}</h3>
                    <p className="text-xs text-gray-400">Total Volume - {activeRoutine.date}</p>
                  </div>
                  <span className="text-xs text-gray-400 flex items-center gap-1">Last 3 months <ChevronDown size={14} /></span>
                </div>

                {/* Line chart mô phỏng biểu đồ Volume động dựa vào Routine được chọn */}
                <div className="h-44 relative mb-4">
                  <svg className="w-full h-full" viewBox="0 0 500 150">
                    {/* Các đường grid ngang */}
                    <line x1="0" y1="25" x2="500" y2="25" stroke="#2c2c2e" strokeWidth="1" />
                    <line x1="0" y1="75" x2="500" y2="75" stroke="#2c2c2e" strokeWidth="1" />
                    <line x1="0" y1="125" x2="500" y2="125" stroke="#2c2c2e" strokeWidth="1" />
                    
                    {/* Vẽ đường line dập dềnh động */}
                    <path 
                      d={activeRoutine.chartPath} 
                      fill="none" 
                      stroke="#0a84ff" 
                      strokeWidth="3" 
                    />
                    
                    {/* Các điểm nút bấm tròn */}
                    {activeRoutine.chartPoints.map((pt, index) => (
                      <circle 
                        key={index} 
                        cx={pt.cx} 
                        cy={pt.cy} 
                        r="5" 
                        fill={pt.isPeak ? "#30d158" : "#0a84ff"} 
                      />
                    ))}
                  </svg>
                  
                  <div className="flex justify-between text-[9px] text-gray-500 px-2 mt-1">
                    <span>Mar 12</span>
                    <span>Mar 19</span>
                    <span>Apr 2</span>
                    <span>Apr 9</span>
                    <span>Apr 16</span>
                    <span>Apr 24</span>
                    <span>May 8</span>
                    <span>{activeRoutine.date}</span>
                  </div>
                </div>

                <div className="flex gap-2 text-xs">
                  <button className="bg-[#0a84ff] text-white px-4 py-1.5 rounded-full font-bold">Volume</button>
                  <button className="bg-[#2c2c2e] text-gray-400 hover:text-white px-4 py-1.5 rounded-full font-bold">Reps</button>
                  <button className="bg-[#2c2c2e] text-gray-400 hover:text-white px-4 py-1.5 rounded-full font-bold">Duration</button>
                </div>
              </div>

              {/* Danh sách Exercises trong routine động */}
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <h3 className="text-sm font-black text-gray-400 uppercase tracking-widest">Exercises</h3>
                  <button className="text-xs text-[#0a84ff] font-bold">Edit Routine</button>
                </div>

                {activeRoutine.exercises.map((ex, exIdx) => (
                  <div 
                    key={exIdx} 
                    onClick={() => handleExerciseClick(ex.name)}
                    className="p-4 bg-[#1c1c1e] border border-[#2c2c2e] hover:border-[#0a84ff] transition-all rounded-xl cursor-pointer"
                  >
                    <div className="flex gap-3 mb-3">
                      <div className="w-10 h-10 rounded-lg bg-gray-800 flex items-center justify-center font-bold text-[#0a84ff] text-xs">
                        {ex.abbr}
                      </div>
                      <div>
                        <h4 className="font-bold text-white text-sm">{ex.name}</h4>
                        <p className="text-xs text-gray-400">{ex.category}</p>
                      </div>
                    </div>
                    <div className="space-y-2 bg-black/40 p-3 rounded-lg text-xs">
                      {ex.sets.map((st, sIdx) => (
                        <div key={sIdx} className="flex justify-between text-gray-400">
                          <span>Set {st.num}</span>
                          <strong className="text-white">{st.weight} x {st.reps}</strong>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

            </div>
          </div>
        )}

        {/* ========================================================== */}
        {/* SCREEN 4: WORKOUT DETAIL "upper" (Giống hệt image_6be3a4/c1)  */}
        {/* ========================================================== */}
        {currentTab === 'workout-detail' && (
          <div className="flex-1 overflow-y-auto min-h-0 w-full custom-scrollbar">
            <div className="p-8 max-w-4xl mx-auto w-full">
              
              <button 
                onClick={() => setCurrentTab('profile')}
                className="flex items-center gap-1.5 text-xs font-bold text-[#0a84ff] mb-6 hover:underline"
              >
                <ChevronLeft size={16} /> Quay lại Profile
              </button>

              {/* Header profile info */}
              <div className="flex items-center gap-3 mb-4">
                <img 
                  src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&h=150&q=80"
                  className="w-10 h-10 rounded-full object-cover border border-[#2c2c2e]"
                  alt="avatar"
                />
                <div>
                  <h4 className="text-sm font-bold text-white">chickenlegg</h4>
                  <p className="text-xs text-gray-400">Monday, May 25, 2026 - 5:00pm</p>
                </div>
              </div>

              {/* Workout Details Title & Stats */}
              <div className="border-b border-[#2c2c2e] pb-5 mb-6">
                <h1 className="text-2xl font-black text-white">upper</h1>
                <div className="flex gap-8 mt-4">
                  <div>
                    <span className="text-xs text-gray-500 uppercase tracking-wider block">Time</span>
                    <strong className="text-lg text-white font-black">1h 5min</strong>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500 uppercase tracking-wider block">Volume</span>
                    <strong className="text-lg text-white font-black">4.325 kg</strong>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500 uppercase tracking-wider block">Sets</span>
                    <strong className="text-lg text-white font-black">15</strong>
                  </div>
                </div>

                <div className="flex gap-4 mt-4">
                  <button className="flex items-center gap-1.5 text-xs bg-[#1c1c1e] px-3.5 py-1.5 rounded-lg text-gray-300 hover:text-white"><ThumbsUp size={13} /> Thích</button>
                  <button className="flex items-center gap-1.5 text-xs bg-[#1c1c1e] px-3.5 py-1.5 rounded-lg text-gray-300 hover:text-white"><MessageSquare size={13} /> Bình luận</button>
                </div>
              </div>

              {/* Muscle Split Progress Bars */}
              <div className="bg-[#1c1c1e] rounded-xl border border-[#2c2c2e] p-5 mb-8">
                <h3 className="text-xs font-black text-gray-400 uppercase tracking-widest mb-4">Muscle Split</h3>
                <div className="space-y-3.5">
                  <div>
                    <div className="flex justify-between text-xs mb-1.5">
                      <span className="text-gray-300 font-semibold">Arms (Tay)</span>
                      <strong className="text-white">38%</strong>
                    </div>
                    <div className="w-full h-2 bg-black rounded-full overflow-hidden">
                      <div className={`bg-[#0a84ff] h-full rounded-full ${barWidthClasses['38%']}`}></div>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-xs mb-1.5">
                      <span className="text-gray-300 font-semibold">Back (Lưng)</span>
                      <strong className="text-white">36%</strong>
                    </div>
                    <div className="w-full h-2 bg-black rounded-full overflow-hidden">
                      <div className={`bg-[#0a84ff] h-full rounded-full ${barWidthClasses['36%']}`}></div>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-xs mb-1.5">
                      <span className="text-gray-300 font-semibold">Chest (Ngực)</span>
                      <strong className="text-white">21%</strong>
                    </div>
                    <div className="w-full h-2 bg-black rounded-full overflow-hidden">
                      <div className={`bg-[#0a84ff] h-full rounded-full ${barWidthClasses['21%']}`}></div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Workout exercises logged list */}
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <h3 className="text-sm font-black text-gray-400 uppercase tracking-widest">Workout Exercises</h3>
                  <span className="text-xs text-yellow-500 bg-yellow-500/10 px-2.5 py-1 rounded-full border border-yellow-500/20">💡 Click vào tên để AI phân tích</span>
                </div>

                {/* Butterfly Pec Deck */}
                <div 
                  onClick={() => handleExerciseClick("Butterfly (Pec Deck)")}
                  className="p-4 bg-[#1c1c1e] border border-[#2c2c2e] hover:border-[#0a84ff] transition-all rounded-xl cursor-pointer"
                >
                  <h4 className="font-bold text-white text-sm mb-3">Butterfly (Pec Deck)</h4>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between text-gray-400">
                      <span>Set 1</span>
                      <strong className="text-white">40 kg x 9 reps</strong>
                    </div>
                    <div className="flex justify-between text-gray-400">
                      <span>Set 2</span>
                      <strong className="text-white">40 kg x 6 reps</strong>
                    </div>
                  </div>
                </div>

                {/* Pendlay Row Barbell */}
                <div 
                  onClick={() => handleExerciseClick("Pendlay Row (Barbell)")}
                  className="p-4 bg-[#1c1c1e] border border-[#2c2c2e] hover:border-[#0a84ff] transition-all rounded-xl cursor-pointer"
                >
                  <h4 className="font-bold text-white text-sm mb-3">Pendlay Row (Barbell)</h4>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between text-gray-400">
                      <span>Set 1</span>
                      <strong className="text-white">50 kg x 10 reps</strong>
                    </div>
                    <div className="flex justify-between text-gray-400">
                      <span>Set 2</span>
                      <strong className="text-white">50 kg x 8 reps</strong>
                    </div>
                  </div>
                </div>

                {/* lat prayer */}
                <div 
                  onClick={() => handleExerciseClick("lat prayer")}
                  className="p-4 bg-[#1c1c1e] border border-[#2c2c2e] hover:border-[#0a84ff] transition-all rounded-xl cursor-pointer"
                >
                  <h4 className="font-bold text-white text-sm mb-3">lat prayer</h4>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between text-gray-400">
                      <span>Set 1</span>
                      <strong className="text-white">40 kg x 11 reps</strong>
                    </div>
                    <div className="flex justify-between text-gray-400">
                      <span>Set 2</span>
                      <strong className="text-white">40 kg x 8 reps</strong>
                    </div>
                  </div>
                </div>

                {/* Overhead Triceps Extension */}
                <div 
                  onClick={() => handleExerciseClick("Overhead Triceps Extension (Cable)")}
                  className="p-4 bg-[#1c1c1e] border border-[#2c2c2e] hover:border-[#0a84ff] transition-all rounded-xl cursor-pointer"
                >
                  <h4 className="font-bold text-white text-sm mb-3">Overhead Triceps Extension (Cable)</h4>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between text-gray-400">
                      <span>Set 1</span>
                      <strong className="text-white">40 kg x 10 reps</strong>
                    </div>
                    <div className="flex justify-between text-gray-400">
                      <span>Set 2</span>
                      <strong className="text-white">40 kg x 8 reps</strong>
                    </div>
                  </div>
                </div>
              </div>

            </div>
          </div>
        )}

        {/* ========================================================== */}
        {/* SCREEN 5: HEVY AI COACH (Dành riêng cho trợ lý)            */}
        {/* ========================================================== */}
        {currentTab === 'coach' && (
          <div className="flex-1 flex flex-col min-h-0 w-full">
            
            {/* Thanh tiêu đề đỉnh Coach */}
            <div className="p-5 border-b border-[#2c2c2e] bg-[#121214] flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-[#007aff]/15 flex items-center justify-center text-[#0a84ff]">
                  <Bot size={22} className="animate-pulse" />
                </div>
                <div>
                  <h2 className="font-bold text-white text-base">Hevy AI Coach 🤖</h2>
                  {selectedExercise ? (
                    <span className="text-xs text-[#0a84ff] font-medium flex items-center gap-1 mt-0.5">
                      <Sparkles size={11} /> Đang phân tích bài: <strong>{selectedExercise}</strong>
                    </span>
                  ) : (
                    <span className="text-xs text-gray-400 block mt-0.5">Sẵn sàng phiên dịch dữ liệu của bạn thành hành động</span>
                  )}
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                <button 
                  onClick={() => {
                    setMessages([{
                      id: Date.now(),
                      sender: 'ai',
                      text: 'Hệ thống đã reset lịch sử trò chuyện. Bạn có thể bắt đầu lại kịch bản phân tích mới!',
                      type: 'text'
                    }]);
                    setSelectedExercise(null);
                  }}
                  className="flex items-center gap-1.5 bg-[#1c1c1e] hover:bg-[#2c2c2e] text-gray-300 text-xs py-1.5 px-3 rounded-lg border border-[#2c2c2e] transition-colors"
                >
                  <RefreshCcw size={13} /> Reset Chat
                </button>
              </div>
            </div>

            {/* Thân log lịch sử đoạn chat */}
            <div className="flex-1 overflow-y-auto min-h-0 p-6 space-y-5 bg-[#08080a] custom-scrollbar">
              
              <div className="max-w-2xl mx-auto space-y-6">
                {messages.map((msg) => (
                  <div 
                    key={msg.id} 
                    className={`flex gap-3.5 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    {msg.sender === 'ai' && (
                      <div className="w-9 h-9 rounded-xl bg-[#0a84ff] flex items-center justify-center text-white flex-shrink-0 shadow-md">
                        <Bot size={16} />
                      </div>
                    )}
                    
                    <div className={`max-w-[85%] p-4 rounded-2xl ${
                      msg.sender === 'user' 
                        ? 'bg-[#0a84ff] text-white rounded-tr-sm' 
                        : 'bg-[#1c1c1e] border border-[#2c2c2e] text-[#f1f1f2] rounded-tl-sm'
                    } shadow-sm text-sm leading-relaxed`}
                    >
                      {msg.text.split('\n\n').map((para, i) => {
                        if (para.startsWith('📊') || para.startsWith('🔥') || para.startsWith('🤔') || para.startsWith('🔍') || para.startsWith('✍️')) {
                          return <p key={i} className="font-bold text-white text-sm mb-2">{para}</p>;
                        }
                        if (para.startsWith('*')) {
                          return (
                            <ul key={i} className="list-disc pl-5 space-y-1 mb-2 text-gray-300">
                              {para.split('\n').map((item, idx) => (
                                <li key={idx}>{item.replace('* ', '')}</li>
                              ))}
                            </ul>
                          );
                        }
                        return <p key={i} className="mb-2 last:mb-0 text-gray-300">{para}</p>;
                      })}
                    </div>

                    {msg.sender === 'user' && (
                      <div className="w-9 h-9 rounded-xl bg-gray-700 flex items-center justify-center text-white flex-shrink-0 shadow-md">
                        <User size={16} />
                      </div>
                    )}
                  </div>
                ))}

                {isTyping && (
                  <div className="flex justify-start animate-pulse">
                    <div className="flex gap-3.5 max-w-[85%]">
                      <div className="w-9 h-9 rounded-xl bg-[#0a84ff] flex items-center justify-center text-white">
                        <Bot size={16} />
                      </div>
                      <div className="bg-[#1c1c1e] p-4 rounded-2xl rounded-tl-sm border border-[#2c2c2e] flex items-center gap-1.5 h-[44px]">
                        <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce delay-0"></div>
                        <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce delay-150"></div>
                        <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce delay-300"></div>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={chatEndRef} />
              </div>

            </div>

            {/* Vùng nhập văn bản trò chuyện */}
            <div className="p-5 bg-[#121214] border-t border-[#2c2c2e]">
              <div className="max-w-2xl mx-auto">
                <form 
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSendMessage(inputText);
                  }}
                  className="relative flex items-center bg-[#1c1c1e] border border-[#2c2c2e] rounded-xl focus-within:border-[#0a84ff] transition-all p-1"
                >
                  <textarea
                    rows={1}
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    placeholder="Hỏi AI Coach: 'Bench press của tôi tiến bộ không?', 'Tập tốt không?'..."
                    className="flex-1 bg-transparent text-[#f1f1f2] placeholder-gray-500 text-sm px-3.5 py-3 outline-none resize-none overflow-hidden max-h-24 custom-scrollbar"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSendMessage(inputText);
                      }
                    }}
                  />
                  <button
                    type="submit"
                    aria-label="Send message"
                    disabled={!inputText.trim()}
                    className="w-10 h-10 rounded-lg bg-[#0a84ff] hover:bg-[#0062cc] disabled:bg-[#1a1a1c] disabled:text-gray-600 text-white flex items-center justify-center transition-all flex-shrink-0"
                  >
                    <Send size={15} />
                  </button>
                </form>
                <div className="flex items-center gap-1.5 text-[10px] text-gray-500 mt-2.5 px-1 justify-between">
                  <span className="flex items-center gap-1"><Info size={11} /> Dữ liệu được tính toán dựa trên 133 workouts thực tế của chickenlegg</span>
                  <span>Nhấn Shift + Enter để xuống dòng</span>
                </div>
              </div>
            </div>

          </div>
        )}

      </main>
    </div>
  );
}