# Graph Report - trading  (2026-07-29)

## Corpus Check
- 60 files · ~51,309 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 997 nodes · 1473 edges · 52 communities (48 shown, 4 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 7 edges (avg confidence: 0.59)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7d2ac6f2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ai_trader.py
- 8. Pengaturan desktop: panduan lengkap
- 8. Pengaturan desktop: panduan lengkap
- 8. Pengaturan desktop: panduan lengkap
- Panduan Lengkap AI Trading Bot untuk Pemula
- Panduan_AI_Trading_Bot_untuk_Pemula_v1.2.2_34dd41b7.md
- 8. Pengaturan desktop: panduan lengkap
- Panduan_AI_Trading_Bot_untuk_Pemula_v1.2.3_0503c9e5.md
- Panduan_AI_Trading_Bot_untuk_Pemula_v1.2.4_05af85a5.md
- TradingDesktop
- trade_logger.py
- risk_manager.py
- Aplikasi Desktop AI Trading
- Panduan Instalasi Bot Trading MT5 untuk Pemula
- 2. Istilah dasar yang harus dipahami
- 2. Istilah dasar yang harus dipahami
- 2. Istilah dasar yang harus dipahami
- 2. Istilah dasar yang harus dipahami
- learner.py
- runtime_guard.py
- Panduan Telegram Bot Trading untuk Pemula
- test_next_stage_guards.py
- main
- mt5_connector.py
- import_learning_csv
- market_filters.py
- run_cycle
- config.py
- main
- export_project_docx.py
- shadow_tracker.py
- DesktopSettingsTests
- position_manager.py
- MomentumDistanceTests
- model_registry.py
- test_mt5_connector.py
- AGENTS.md
- 14. Data yang disimpan
- TechnicalConfluenceTests
- historical_learning.py
- 4. Tiga cara bot melakukan entry
- 5. Indikator yang digunakan
- 9. Arti tiga preset
- 14. Data yang disimpan
- 4. Tiga cara bot melakukan entry
- 5. Indikator yang digunakan
- 9. Arti tiga preset
- 6. Bagaimana AI belajar
- test_mt5_connector.py

## God Nodes (most connected - your core abstractions)
1. `run_cycle()` - 52 edges
2. `8. Pengaturan desktop: panduan lengkap` - 44 edges
3. `8. Pengaturan desktop: panduan lengkap` - 44 edges
4. `8. Pengaturan desktop: panduan lengkap` - 44 edges
5. `8. Pengaturan desktop: panduan lengkap` - 40 edges
6. `Panduan Lengkap AI Trading Bot untuk Pemula` - 26 edges
7. `2. Istilah dasar yang harus dipahami` - 25 edges
8. `2. Istilah dasar yang harus dipahami` - 25 edges
9. `2. Istilah dasar yang harus dipahami` - 25 edges
10. `2. Istilah dasar yang harus dipahami` - 25 edges

## Surprising Connections (you probably didn't know these)
- `decide()` --indirect_call--> `signal()`  [INFERRED]
  learner.py → tests/test_hybrid_strategy.py
- `get_closed_deal_by_position()` --indirect_call--> `volume()`  [INFERRED]
  mt5_connector.py → technical_strategies.py
- `TradeSignal` --uses--> `TechnicalSignal`  [INFERRED]
  strategy.py → technical_strategies.py
- `FVGZone` --uses--> `TechnicalSignal`  [INFERRED]
  strategy.py → technical_strategies.py
- `ModelPrediction` --uses--> `TradeSignal`  [INFERRED]
  ai_trader.py → strategy.py

## Import Cycles
- None detected.

## Communities (52 total, 4 thin omitted)

### Community 0 - "ai_trader.py"
Cohesion: 0.06
Nodes (57): _create_model(), extract_features(), _load_model(), load_training_samples(), model_status(), ModelPrediction, predict(), predict_score() (+49 more)

### Community 1 - "8. Pengaturan desktop: panduan lengkap"
Cohesion: 0.05
Nodes (44): 8.0 Folder data terpadu, 8.10 Take Profit × ATR, 8.11 Jarak minimum entry (ATR), 8.11a Jarak maksimum momentum (ATR), 8.11b Tambahan threshold mode probe, 8.11c Tambahan threshold spread tinggi, 8.11d Tambahan threshold spread sangat tinggi, 8.12 EMA tren cepat (+36 more)

### Community 2 - "8. Pengaturan desktop: panduan lengkap"
Cohesion: 0.05
Nodes (44): 8.0 Folder data terpadu, 8.10 Take Profit × ATR, 8.11 Jarak minimum entry (ATR), 8.11a Jarak maksimum momentum (ATR), 8.11b Tambahan threshold mode probe, 8.11c Tambahan threshold spread tinggi, 8.11d Tambahan threshold spread sangat tinggi, 8.12 EMA tren cepat (+36 more)

### Community 3 - "8. Pengaturan desktop: panduan lengkap"
Cohesion: 0.05
Nodes (44): 8.0 Folder data terpadu, 8.10 Take Profit × ATR, 8.11 Jarak minimum entry (ATR), 8.11a Jarak maksimum momentum (ATR), 8.11b Tambahan threshold mode probe, 8.11c Tambahan threshold spread tinggi, 8.11d Tambahan threshold spread sangat tinggi, 8.12 EMA tren cepat (+36 more)

### Community 4 - "Panduan Lengkap AI Trading Bot untuk Pemula"
Cohesion: 0.05
Nodes (40): 10. Pengaturan yang saling berhubungan, 11. Filter spread bertingkat, 12. Pengamanan kerugian, 13. Cooldown yang berlaku, 14. Data yang disimpan, 15. Cara memahami win rate, 16. Telegram untuk orang awam, 17. Berita ekonomi (+32 more)

### Community 5 - "Panduan_AI_Trading_Bot_untuk_Pemula_v1.2.2_34dd41b7.md"
Cohesion: 0.11
Nodes (18): 10. Pengaturan yang saling berhubungan, 11. Filter spread bertingkat, 12. Pengamanan kerugian, 13. Cooldown yang berlaku, 15. Cara memahami win rate, 16. Telegram untuk orang awam, 17. Berita ekonomi, 18. Cara menjalankan desktop (+10 more)

### Community 6 - "8. Pengaturan desktop: panduan lengkap"
Cohesion: 0.05
Nodes (40): 8.0 Folder data terpadu, 8.10 Take Profit × ATR, 8.11 Jarak minimum entry (ATR), 8.12 EMA tren cepat, 8.13 EMA tren lambat, 8.14 EMA entry cepat, 8.15 EMA entry lambat, 8.16 Periode RSI (+32 more)

### Community 7 - "Panduan_AI_Trading_Bot_untuk_Pemula_v1.2.3_0503c9e5.md"
Cohesion: 0.05
Nodes (39): 10. Pengaturan yang saling berhubungan, 11. Filter spread bertingkat, 12. Pengamanan kerugian, 13. Cooldown yang berlaku, 14. Data yang disimpan, 15. Cara memahami win rate, 16. Telegram untuk orang awam, 17. Berita ekonomi (+31 more)

### Community 8 - "Panduan_AI_Trading_Bot_untuk_Pemula_v1.2.4_05af85a5.md"
Cohesion: 0.05
Nodes (39): 10. Pengaturan yang saling berhubungan, 11. Filter spread bertingkat, 12. Pengamanan kerugian, 13. Cooldown yang berlaku, 14. Data yang disimpan, 15. Cara memahami win rate, 16. Telegram untuk orang awam, 17. Berita ekonomi (+31 more)

### Community 9 - "TradingDesktop"
Cohesion: 0.11
Nodes (12): choose_runtime_root(), process_command(), Path, Aplikasi desktop Windows untuk mengendalikan engine trading., Simpan setting pada HKCU\\Environment tanpa menulis secret ke project., save_user_environment(), TradingDesktop, validate_settings() (+4 more)

### Community 10 - "trade_logger.py"
Cohesion: 0.08
Nodes (24): TradeLoggerRepairTests, clean_trade_log(), _ensure_file(), ensure_log_files(), get_entry_trade_info(), load_closed_trades(), log_closed_trade(), log_trade() (+16 more)

### Community 11 - "risk_manager.py"
Cohesion: 0.15
Nodes (16): build_order_plan(), calculate_lot_size(), calculate_total_open_risk_percent(), can_open_direction(), can_open_new_position(), can_open_within_risk_budget(), OrderPlan, risk_manager.py Menghitung ukuran lot berdasarkan % risiko equity, menentukan SL (+8 more)

### Community 12 - "Aplikasi Desktop AI Trading"
Cohesion: 0.20
Nodes (10): Aplikasi Desktop AI Trading, Aturan jumlah posisi, Fitur, Instalasi di komputer lain, Keamanan, Membuat file EXE, Menjalankan dari source code, Pemakaian pertama (+2 more)

### Community 13 - "Panduan Instalasi Bot Trading MT5 untuk Pemula"
Cohesion: 0.10
Nodes (20): 10. Pasang notifikasi Telegram, 11. Jalankan pemeriksaan project, 12. Jalankan bot, 13. Memahami alasan bot tidak entry, 14. File data lokal, 15. Pembelajaran AI, 16. Blackout berita opsional, 17. Update project dari GitHub (+12 more)

### Community 14 - "2. Istilah dasar yang harus dipahami"
Cohesion: 0.08
Nodes (25): 2. Istilah dasar yang harus dipahami, API, Balance dan equity, Break-even, Broker, BUY, Chart dan candle, Close (+17 more)

### Community 15 - "2. Istilah dasar yang harus dipahami"
Cohesion: 0.08
Nodes (25): 2. Istilah dasar yang harus dipahami, API, Balance dan equity, Break-even, Broker, BUY, Chart dan candle, Close (+17 more)

### Community 16 - "2. Istilah dasar yang harus dipahami"
Cohesion: 0.08
Nodes (25): 2. Istilah dasar yang harus dipahami, API, Balance dan equity, Break-even, Broker, BUY, Chart dan candle, Close (+17 more)

### Community 17 - "2. Istilah dasar yang harus dipahami"
Cohesion: 0.08
Nodes (25): 2. Istilah dasar yang harus dipahami, API, Balance dan equity, Break-even, Broker, BUY, Chart dan candle, Close (+17 more)

### Community 18 - "learner.py"
Cohesion: 0.10
Nodes (21): audit(), Audit log trading sebelum learner atau model ML memakai datanya., _blend_metrics(), build_adaptive_risk_percent(), calculate_trade_metrics(), compute_entry_score(), decide(), estimate_market_score() (+13 more)

### Community 19 - "runtime_guard.py"
Cohesion: 0.08
Nodes (30): main(), notify_bot_started(), notify_bot_stopped(), notify_daily_drawdown_hit(), notify_error(), notify_trade_closed(), notify_trade_opened(), notifier.py Mengirim notifikasi ke Telegram saat bot start, stop, error, atau ke (+22 more)

### Community 20 - "Panduan Telegram Bot Trading untuk Pemula"
Cohesion: 0.09
Nodes (22): 1. Buat bot melalui BotFather, 2. Mulai chat dengan bot, 3. Dapatkan Chat ID, 4. Chat ID grup opsional, 5. Simpan token dan Chat ID sementara, 6. Tes pengiriman pesan, 7. Simpan konfigurasi permanen, 8. Jalankan bot trading (+14 more)

### Community 21 - "test_next_stage_guards.py"
Cohesion: 0.12
Nodes (10): event_blackout(), is_blackout(), _parse_time(), datetime, Filter kalender ekonomi opsional dengan cache; sumber API dipilih pengguna., ExecutionGuardTests, ExposureTests, NewsFilterTests (+2 more)

### Community 23 - "mt5_connector.py"
Cohesion: 0.13
Nodes (22): Validasi kondisi broker dan margin sebelum market order dikirim., validate_market_order(), calculate_order_margin(), get_account_info(), get_closed_deal_by_position(), get_current_prices(), get_open_positions(), get_position_ticket_from_deal() (+14 more)

### Community 24 - "import_learning_csv"
Cohesion: 0.25
Nodes (13): export_learning_csv(), import_learning_csv(), merge_csv_history(), merge_learning_history(), Path, Penyatuan histori trading dari instalasi/project lama secara aman., Import CSV pilihan pengguna; hanya nama dan skema histori resmi diterima., Ekspor CSV pengalaman tanpa kredensial, system log, atau data konfigurasi. (+5 more)

### Community 25 - "market_filters.py"
Cohesion: 0.14
Nodes (9): check_spread(), check_volatility(), in_news_blackout(), DataFrame, datetime, Filter spread, volatilitas, blackout berita manual, cooldown, dan loss streak., recent_trade_guard(), spread_metrics() (+1 more)

### Community 26 - "run_cycle"
Cohesion: 0.18
Nodes (12): is_within_trading_hours(), print_status(), main.py Loop utama bot trading. Menjalankan siklus sesuai diagram alur: 1. Cek s, Cetak perubahan status; status sama diulang berkala agar bot tampak aktif., Menjalankan satu siklus pengecekan penuh. Mengembalikan set tiket posisi terbuka, run_cycle(), evaluate(), Pantau kualitas probabilitas model pada hasil trade terbaru. (+4 more)

### Community 27 - "config.py"
Cohesion: 0.15
Nodes (4): config.py Semua parameter sistem trading terpusat di sini. Ubah angka di file in, diagnose_trade_disabled.py Mengecek 3 kemungkinan penyebab error retcode 10017 ", diagnose_trade_disabled_v2.py Memaksa symbol_select dulu (memastikan simbol akti, Ringkasan performa trading dari log lokal yang sudah tervalidasi.

### Community 29 - "export_project_docx.py"
Cohesion: 0.32
Nodes (11): Document, add_code_block(), add_inline(), add_page_number(), add_table(), configure_document(), export(), Path (+3 more)

### Community 30 - "shadow_tracker.py"
Cohesion: 0.25
Nodes (8): DataFrame, Catat hasil virtual sinyal AI yang diterima dan ditolak tanpa mengirim order., Selesaikan simulasi SL/TP; bila keduanya kena satu candle, hitung loss., _read(), record(), resolve(), _write(), ShadowTrackerTests

### Community 31 - "DesktopSettingsTests"
Cohesion: 0.40
Nodes (3): promote(), Versioning, promotion, dan rollback model ML., _reject()

### Community 32 - "position_manager.py"
Cohesion: 0.33
Nodes (3): manage(), Break-even dan trailing stop yang hanya menggeser SL ke arah lebih aman., PositionManagerTests

### Community 33 - "MomentumDistanceTests"
Cohesion: 0.23
Nodes (4): FVGTests, HybridDecisionTests, DataFrame, signal()

### Community 34 - "model_registry.py"
Cohesion: 0.22
Nodes (12): estimate_spread_cost(), fetch_backtest_data(), prepare_h1_bias(), print_summary(), DataFrame, backtest.py Menjalankan strategi terhadap data historis MT5 untuk mendapatkan es, Perkiraan biaya spread per trade di lot minimum, pakai spread SAAT INI sebagai p, run_backtest() (+4 more)

### Community 35 - "test_mt5_connector.py"
Cohesion: 0.43
Nodes (18): candlestick(), displacement(), evaluate_all(), liquidity(), market_structure(), _neutral(), order_block(), _pivots() (+10 more)

### Community 39 - "14. Data yang disimpan"
Cohesion: 0.15
Nodes (17): main(), check_min_capital.py Menghitung modal minimum yang dibutuhkan supaya risk manage, main(), dry_run.py Menjalankan logika strategi & risk management dengan data LIVE dari M, generate(), Replay strategi A-L dan tulis hanya setup yang outcome-nya sudah diketahui., connect(), disconnect() (+9 more)

### Community 40 - "TechnicalConfluenceTests"
Cohesion: 0.22
Nodes (4): frame(), IndependentDetectorTests, DataFrame, TechnicalConfluenceTests

### Community 41 - "historical_learning.py"
Cohesion: 0.25
Nodes (4): _outcome(), DataFrame, Bangun dataset sinyal historis dari candle tertutup tanpa look-ahead fitur., HistoricalOutcomeTests

### Community 42 - "4. Tiga cara bot melakukan entry"
Cohesion: 0.20
Nodes (10): Bot Trading XAUUSD untuk MT5, Cara AI belajar, Instalasi cepat, Keterbatasan, Konfigurasi, Menjalankan, PERINGATAN PENTING, Strategi modular A-L (+2 more)

### Community 43 - "5. Indikator yang digunakan"
Cohesion: 0.25
Nodes (8): Aktivasi `.venv` ditolak, Bot berhenti karena drawdown, Koneksi MT5 gagal, Menjalankan tanpa aktivasi `.venv`, `ModuleNotFoundError`, `Order plan ditolak` atau `lot minimum`, `python` tidak dikenali, Troubleshooting

### Community 44 - "9. Arti tiga preset"
Cohesion: 0.33
Nodes (6): Build gagal pada PyInstaller, EXE tidak dapat menulis log, First-run langsung diblokir drawdown besar, Tes MT5 gagal, Tombol Start langsung kembali berhenti, Troubleshooting

### Community 46 - "14. Data yang disimpan"
Cohesion: 0.33
Nodes (6): 14. Data yang disimpan, closed_trade_log.csv, runtime_state.json, shadow_signal_log.csv, system_log.csv, trade_log.csv

### Community 47 - "4. Tiga cara bot melakukan entry"
Cohesion: 0.50
Nodes (4): 4. Tiga cara bot melakukan entry, Continuation atau mengikuti tren, Crossover atau persilangan, Momentum

### Community 48 - "5. Indikator yang digunakan"
Cohesion: 0.50
Nodes (4): 5. Indikator yang digunakan, ATR, EMA, RSI

### Community 49 - "9. Arti tiga preset"
Cohesion: 0.50
Nodes (4): 9. Arti tiga preset, Aktif, Konservatif, Seimbang

### Community 50 - "6. Bagaimana AI belajar"
Cohesion: 0.67
Nodes (3): 6. Bagaimana AI belajar, Model machine learning, Pembelajaran statistik

## Knowledge Gaps
- **470 isolated node(s):** `graphify`, `Fitur`, `Menjalankan dari source code`, `Pemakaian pertama`, `Membuat file EXE` (+465 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `_technical_payload()` connect `ai_trader.py` to `TradingDesktop`, `test_mt5_connector.py`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Why does `run_cycle()` connect `run_cycle` to `ai_trader.py`, `position_manager.py`, `model_registry.py`, `14. Data yang disimpan`, `trade_logger.py`, `risk_manager.py`, `learner.py`, `runtime_guard.py`, `test_next_stage_guards.py`, `mt5_connector.py`, `market_filters.py`, `shadow_tracker.py`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **What connects `graphify`, `Fitur`, `Menjalankan dari source code` to the rest of the system?**
  _470 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `ai_trader.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06277436347673397 - nodes in this community are weakly interconnected._
- **Should `8. Pengaturan desktop: panduan lengkap` be split into smaller, more focused modules?**
  _Cohesion score 0.045454545454545456 - nodes in this community are weakly interconnected._
- **Should `8. Pengaturan desktop: panduan lengkap` be split into smaller, more focused modules?**
  _Cohesion score 0.045454545454545456 - nodes in this community are weakly interconnected._
- **Should `8. Pengaturan desktop: panduan lengkap` be split into smaller, more focused modules?**
  _Cohesion score 0.045454545454545456 - nodes in this community are weakly interconnected._