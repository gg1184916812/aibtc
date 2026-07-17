# core/ai/trading_mentor_ai.py
"""
🧠 AI Trading Mentor - Mentor Digital untuk Trader Indonesia
Sistem AI yang memberikan bimbingan personal seperti mentor manusia
Khusus dirancang untuk trader pemula Indonesia
"""

import datetime
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class TradingSession:
    """Data sesi trading untuk analisis AI"""
    date: datetime.date
    trades: List[Dict]
    emotions: str
    market_conditions: str
    profit_loss: float
    notes: str

class IndonesianTradingMentorAI:
    """AI Mentor Trading dalam Bahasa Indonesia"""
    
    def __init__(self):
        self.personality = "supportive_indonesian_mentor"
        self.language = "bahasa_indonesia"
        self.cultural_context = "indonesian_trading_psychology"
        
    def analyze_trading_session(self, session: TradingSession) -> Dict[str, Any]:
        """Analisis sesi trading seperti mentor berpengalaman"""
        
        analysis = {
            'pola_trading': self._detect_trading_patterns(session),
            'emosi_vs_performa': self._analyze_emotional_impact(session),
            'manajemen_risiko': self._evaluate_risk_management(session),
            'rekomendasi': self._generate_recommendations(session),
            'motivasi': self._create_motivation_message(session)
        }
        
        return analysis
    
    def _detect_trading_patterns(self, session: TradingSession) -> Dict[str, str]:
        """Deteksi pola trading dalam bahasa yang mudah dipahami"""
        
        if session.profit_loss > 0:
            return {
                'pola_utama': 'Trading Disiplin',
                'analisis': f'Bagus! Anda berhasil profit ${session.profit_loss:.2f} hari ini. '
                           f'Saya melihat Anda mengikuti aturan dengan baik.',
                'kekuatan': 'Konsisten dengan strategi yang dipilih',
                'area_perbaikan': 'Pertahankan kedisiplinan ini'
            }
        else:
            return {
                'pola_utama': 'Pembelajaran Berlanjut',
                'analisis': f'Loss ${abs(session.profit_loss):.2f} adalah bagian dari belajar. '
                           f'Yang penting adalah kita belajar dari kesalahan.',
                'kekuatan': 'Berani mengambil risiko untuk belajar',
                'area_perbaikan': 'Mari analisis apa yang bisa diperbaiki'
            }
    
    def _analyze_emotional_impact(self, session: TradingSession) -> Dict[str, str]:
        """Analisis dampak emosi terhadap trading"""
        
        emotional_analysis = {
            'tenang': {
                'feedback': 'Luar biasa! Emosi yang tenang menghasilkan keputusan trading yang objektif.',
                'tip': 'Pertahankan ketenangan ini. Ini adalah kunci trader profesional.'
            },
            'serakah': {
                'feedback': 'Hati-hati! Keserakahan bisa membuat kita mengambil risiko berlebihan.',
                'tip': 'Ingat: "Profit sedikit tapi konsisten lebih baik daripada profit besar sekali terus loss."'
            },
            'takut': {
                'feedback': 'Wajar merasa takut, terutama sebagai pemula. Ini tanda Anda berhati-hati.',
                'tip': 'Mulai dengan lot size kecil dulu. Kepercayaan diri akan tumbuh seiring pengalaman.'
            },
            'frustasi': {
                'feedback': 'Frustasi itu normal ketika trading tidak sesuai harapan.',
                'tip': 'Istirahat dulu, minum kopi, tarik napas. Trading dengan emosi negatif berbahaya.'
            }
        }
        
        emotion = session.emotions.lower()
        return emotional_analysis.get(emotion, {
            'feedback': 'Bagaimana perasaan Anda hari ini? Emosi sangat mempengaruhi performa trading.',
            'tip': 'Selalu cek kondisi emosi sebelum membuka posisi.'
        })
    
    def _evaluate_risk_management(self, session: TradingSession) -> Dict[str, str]:
        """Evaluasi manajemen risiko dalam konteks Indonesia"""
        
        # Simulasi evaluasi berdasarkan trades
        risk_score = self._calculate_risk_score(session.trades)
        
        if risk_score >= 8:
            return {
                'nilai': f'{risk_score}/10 - EXCELLENT!',
                'feedback': 'Manajemen risiko Anda sudah sangat bagus! Seperti trader profesional.',
                'detail': 'Anda konsisten dengan stop loss, lot size wajar, dan tidak over-trading.',
                'apresiasi': 'Dengan disiplin seperti ini, Anda pasti akan sukses jangka panjang! 🎯'
            }
        elif risk_score >= 6:
            return {
                'nilai': f'{risk_score}/10 - GOOD',
                'feedback': 'Manajemen risiko cukup baik, tapi masih ada yang bisa diperbaiki.',
                'detail': 'Kadang lot size agak besar, atau stop loss terlalu jauh.',
                'saran': 'Ingat prinsip: "Jangan pernah risiko lebih dari 2% modal per trade."'
            }
        else:
            return {
                'nilai': f'{risk_score}/10 - PERLU PERBAIKAN',
                'feedback': 'Manajemen risiko perlu diperbaiki agar modal tetap aman.',
                'detail': 'Lot size terlalu besar atau tidak pakai stop loss konsisten.',
                'peringatan': '⚠️ Ingat: "Modal adalah nyawa trader. Jaga baik-baik!"'
            }
    
    def _calculate_risk_score(self, trades: List[Dict]) -> int:
        """Hitung skor risiko dari trades"""
        if not trades:
            return 5
            
        # Simulasi perhitungan risiko
        risk_factors = []
        for trade in trades:
            if trade.get('stop_loss_used', False):
                risk_factors.append(2)  # Good risk management
            if trade.get('lot_size', 0) <= 0.01:
                risk_factors.append(2)  # Conservative lot size
            if trade.get('risk_percent', 0) <= 2:
                risk_factors.append(2)  # Safe risk percentage
                
        return min(10, sum(risk_factors))
    
    def _generate_recommendations(self, session: TradingSession) -> List[str]:
        """Generate rekomendasi spesifik dalam bahasa Indonesia"""
        
        recommendations = [
            "💡 **Tips Hari Ini:**"
        ]
        
        # Rekomendasi berdasarkan performa
        if session.profit_loss > 100:
            recommendations.extend([
                "- Profit bagus! Jangan serakah, ambil sebagian profit untuk disyukuri.",
                "- Pertahankan strategi yang sama, jangan ganti-ganti.",
                "- Dokumentasikan apa yang membuat Anda sukses hari ini."
            ])
        elif session.profit_loss > 0:
            recommendations.extend([
                "- Profit kecil tetap profit! Konsistensi adalah kunci.",
                "- Evaluasi apakah bisa tingkatkan profit dengan risiko yang sama.",
                "- Bagus sekali bisa positif, teruskan!"
            ])
        else:
            recommendations.extend([
                "- Loss adalah guru terbaik. Apa yang bisa dipelajari?",
                "- Cek lagi: apakah analisis teknikal sudah benar?",
                "- Jangan revenge trading! Istirahat dulu jika perlu."
            ])
            
        # Rekomendasi umum untuk trader Indonesia
        recommendations.extend([
            "",
            "🎯 **Fokus Minggu Depan:**",
            "- Trading hanya saat market Jakarta aktif (09:00-16:00 WIB) kalau masih pemula",
            "- Hindari trading saat Jumat sore (market volatile menjelang weekend)",
            "- Pelajari kalender ekonomi Indonesia (pengumuman BI rate, inflasi, dll)",
            "- Join komunitas trader Indonesia untuk sharing pengalaman"
        ])
        
        return recommendations
    
    def _create_motivation_message(self, session: TradingSession) -> str:
        """Pesan motivasi seperti mentor Indonesia yang supportif"""
        
        motivational_messages = {
            'profit_besar': [
                "Luar biasa! Anda sudah menunjukkan potensi trader yang hebat! 🚀",
                "Profit hari ini membuktikan bahwa pembelajaran Anda berbuah hasil!",
                "Terus pertahankan kedisiplinan ini, masa depan trading Anda cerah!"
            ],
            'profit_kecil': [
                "Profit kecil tetap profit! Seperti pepatah: 'Sedikit demi sedikit, lama-lama menjadi bukit' 💪",
                "Konsistensi mengalahkan profit besar sekali. Anda di jalan yang benar!",
                "Warren Buffett juga mulai dari profit kecil. Terus semangat!"
            ],
            'loss_kecil': [
                "Loss kecil adalah investasi untuk ilmu. Trader sukses pasti pernah loss! 📚",
                "Yang penting bukan tidak pernah loss, tapi belajar dari setiap loss.",
                "Ingat: 'Kegagalan adalah kesuksesan yang tertunda'. Terus belajar!"
            ],
            'loss_besar': [
                "Ini pelajaran berharga. Trader terbaik Indonesia juga pernah mengalami ini. 💪",
                "Jangan menyerah! Michael Jordan juga pernah gagal ribuan kali sebelum sukses.",
                "Evaluasi, perbaiki, dan comeback lebih kuat! Saya percaya Anda bisa!"
            ]
        }
        
        # Tentukan kategori berdasarkan profit/loss
        if session.profit_loss > 100:
            category = 'profit_besar'
        elif session.profit_loss > 0:
            category = 'profit_kecil'
        elif session.profit_loss > -50:
            category = 'loss_kecil'
        else:
            category = 'loss_besar'
            
        import random
        message = random.choice(motivational_messages[category])
        
        # Tambahkan konteks personal
        additional_context = self._add_personal_context(session)
        
        return f"{message}\n\n{additional_context}"
    
    def _add_personal_context(self, session: TradingSession) -> str:
        """Tambahkan konteks personal berdasarkan journey user"""
        
        context_messages = [
            "🎯 **Ingat Journey Anda:** Dari awalnya ikut mentor yang hilang kontak, "
            "sekarang Anda sudah bisa trading mandiri dengan sistem sendiri!",
            
            "💡 **Pencapaian Anda:** Demo account $4,649.94 profit bukan main-main! "
            "Ini bukti Anda sudah paham konsep trading.",
            
            "🇮🇩 **Visi Besar:** Anda sedang membangun sistem yang akan membantu "
            "trader pemula Indonesia. Setiap pengalaman hari ini adalah pelajaran untuk mereka!",
            
            "🚀 **Level Up:** Dengan konsistensi seperti ini, soon Anda bisa "
            "upgrade ke live account dan mulai earning real money!"
        ]
        
        import random
        return random.choice(context_messages)
    
    def generate_daily_report(self, session: TradingSession) -> str:
        """Generate laporan harian lengkap dalam Bahasa Indonesia"""
        
        analysis = self.analyze_trading_session(session)
        
        report = f"""
🤖 **LAPORAN MENTOR AI TRADING - {session.date.strftime('%d %B %Y')}**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **RINGKASAN HARI INI:**
• Profit/Loss: ${session.profit_loss:.2f}
• Jumlah Trade: {len(session.trades)}
• Kondisi Emosi: {session.emotions.title()}
• Kondisi Market: {session.market_conditions}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 **ANALISIS POLA TRADING:**
{analysis['pola_trading']['analisis']}

**Kekuatan Anda:** {analysis['pola_trading']['kekuatan']}
**Yang Perlu Diperbaiki:** {analysis['pola_trading']['area_perbaikan']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🧠 **ANALISIS EMOSI vs PERFORMA:**
{analysis['emosi_vs_performa']['feedback']}

💡 **Tip Emosi:** {analysis['emosi_vs_performa']['tip']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛡️ **EVALUASI MANAJEMEN RISIKO:**
**Skor:** {analysis['manajemen_risiko']['nilai']}
{analysis['manajemen_risiko']['feedback']}

{analysis['manajemen_risiko'].get('detail', '')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{chr(10).join(analysis['rekomendasi'])}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💪 **PESAN MOTIVASI:**
{analysis['motivasi']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 **CATATAN PRIBADI ANDA:**
"{session.notes if session.notes else 'Tidak ada catatan hari ini'}"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 **RENCANA BESOK:**
• Fokus pada perbaikan yang disarankan
• Pertahankan yang sudah bagus
• Trading dengan emosi yang tenang
• Ingat: "Konsistensi mengalahkan perfeksi!"

Semangat trading! Mentor AI Anda akan selalu mendampingi! 🚀🇮🇩

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        
        return report.strip()

# Contoh penggunaan untuk demo
def demo_mentor_ai():
    """Demo bagaimana AI Mentor bekerja"""
    
    mentor = IndonesianTradingMentorAI()
    
    # Simulasi sesi trading yang sukses
    successful_session = TradingSession(
        date=datetime.date.today(),
        trades=[
            {'symbol': 'EURUSD', 'profit': 45.50, 'stop_loss_used': True, 'lot_size': 0.01, 'risk_percent': 1.0},
            {'symbol': 'XAUUSD', 'profit': 32.20, 'stop_loss_used': True, 'lot_size': 0.01, 'risk_percent': 1.5},
        ],
        emotions="tenang",
        market_conditions="trending",
        profit_loss=77.70,
        notes="Hari ini fokus pada EURUSD dan XAUUSD. Pakai stop loss ketat dan lot size kecil. Alhamdulillah profit!"
    )
    
    # Simulasi sesi trading yang kurang berhasil
    learning_session = TradingSession(
        date=datetime.date.today(),
        trades=[
            {'symbol': 'GBPUSD', 'profit': -25.30, 'stop_loss_used': False, 'lot_size': 0.02, 'risk_percent': 3.0},
            {'symbol': 'USDJPY', 'profit': -15.80, 'stop_loss_used': True, 'lot_size': 0.01, 'risk_percent': 2.0},
        ],
        emotions="frustasi",
        market_conditions="sideways",
        profit_loss=-41.10,
        notes="Agak emosi hari ini karena loss. Lupa pakai stop loss di GBPUSD. Harus lebih disiplin!"
    )
    
    return mentor, successful_session, learning_session

if __name__ == "__main__":
    # Demo untuk showcase
    mentor, success_session, learning_session = demo_mentor_ai()
    
    print("=== DEMO: SESI TRADING SUKSES ===")
    print(mentor.generate_daily_report(success_session))
    
    print("\n\n" + "="*80 + "\n\n")
    
    print("=== DEMO: SESI PEMBELAJARAN ===")
    print(mentor.generate_daily_report(learning_session))