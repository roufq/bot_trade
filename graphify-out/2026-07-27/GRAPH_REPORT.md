# Graph Report - trading  (2026-07-27)

## Corpus Check
- 55 files · ~45,295 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 900 nodes · 1234 edges · 39 communities (34 shown, 5 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 1 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ce61f251`
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

## God Nodes (most connected - your core abstractions)
1. `run_cycle()` - 48 edges
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
- `ModelPrediction` --uses--> `TradeSignal`  [INFERRED]
  ai_trader.py → strategy.py
- `run_cycle()` --calls--> `extract_features()`  [EXTRACTED]
  main.py → ai_trader.py
- `run_cycle()` --calls--> `predict()`  [EXTRACTED]
  main.py → ai_trader.py
- `train_model()` --calls--> `validate_closed_trade_history()`  [EXTRACTED]
  ai_trader.py → learner.py
- `main()` --calls--> `train_model()`  [EXTRACTED]
  retrain_model.py → ai_trader.py

## Import Cycles
- None detected.

## Communities (39 total, 5 thin omitted)

### Community 0 - "ai_trader.py"
Cohesion: 0.08
Nodes (43): _create_model(), extract_features(), _load_model(), ModelPrediction, predict(), predict_score(), _prepare_dataframe_from_trade_log(), DataFrame (+35 more)

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
Cohesion: 0.05
Nodes (39): 10. Pengaturan yang saling berhubungan, 11. Filter spread bertingkat, 12. Pengamanan kerugian, 13. Cooldown yang berlaku, 14. Data yang disimpan, 15. Cara memahami win rate, 16. Telegram untuk orang awam, 17. Berita ekonomi (+31 more)

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
Nodes (11): choose_runtime_root(), process_command(), Path, Aplikasi desktop Windows untuk mengendalikan engine trading., Simpan setting pada HKCU\\Environment tanpa menulis secret ke project., save_user_environment(), TradingDesktop, validate_settings() (+3 more)

### Community 10 - "trade_logger.py"
Cohesion: 0.08
Nodes (24): TradeLoggerRepairTests, clean_trade_log(), _ensure_file(), ensure_log_files(), get_entry_trade_info(), load_closed_trades(), log_closed_trade(), log_trade() (+16 more)

### Community 11 - "risk_manager.py"
Cohesion: 0.08
Nodes (20): build_order_plan(), calculate_lot_size(), calculate_total_open_risk_percent(), can_open_direction(), can_open_new_position(), can_open_within_risk_budget(), check_daily_drawdown(), OrderPlan (+12 more)

### Community 12 - "Aplikasi Desktop AI Trading"
Cohesion: 0.08
Nodes (24): Aplikasi Desktop AI Trading, Aturan jumlah posisi, Build gagal pada PyInstaller, EXE tidak dapat menulis log, Fitur, Instalasi di komputer lain, Keamanan, Membuat file EXE (+16 more)

### Community 13 - "Panduan Instalasi Bot Trading MT5 untuk Pemula"
Cohesion: 0.07
Nodes (28): 10. Pasang notifikasi Telegram, 11. Jalankan pemeriksaan project, 12. Jalankan bot, 13. Memahami alasan bot tidak entry, 14. File data lokal, 15. Pembelajaran AI, 16. Blackout berita opsional, 17. Update project dari GitHub (+20 more)

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
Cohesion: 0.17
Nodes (19): audit(), Audit log trading sebelum learner atau model ML memakai datanya., _blend_metrics(), build_adaptive_risk_percent(), calculate_trade_metrics(), compute_entry_score(), decide(), estimate_market_score() (+11 more)

### Community 19 - "runtime_guard.py"
Cohesion: 0.16
Nodes (13): get_daily_start_equity(), get_tracked_tickets(), load_state(), order_circuit_status(), datetime, Single-instance lock dan state risiko yang bertahan setelah restart., Ambil baseline equity harian yang tidak berubah ketika bot di-restart., record_order_result() (+5 more)

### Community 20 - "Panduan Telegram Bot Trading untuk Pemula"
Cohesion: 0.09
Nodes (22): 1. Buat bot melalui BotFather, 2. Mulai chat dengan bot, 3. Dapatkan Chat ID, 4. Chat ID grup opsional, 5. Simpan token dan Chat ID sementara, 6. Tes pengiriman pesan, 7. Simpan konfigurasi permanen, 8. Jalankan bot trading (+14 more)

### Community 21 - "test_next_stage_guards.py"
Cohesion: 0.12
Nodes (10): event_blackout(), is_blackout(), _parse_time(), datetime, Filter kalender ekonomi opsional dengan cache; sumber API dipilih pengguna., ExecutionGuardTests, ExposureTests, NewsFilterTests (+2 more)

### Community 22 - "main"
Cohesion: 0.14
Nodes (17): main(), check_min_capital.py Menghitung modal minimum yang dibutuhkan supaya risk manage, main(), dry_run.py Menjalankan logika strategi & risk management dengan data LIVE dari M, connect(), disconnect(), get_account_info(), get_rates() (+9 more)

### Community 23 - "mt5_connector.py"
Cohesion: 0.15
Nodes (18): Validasi kondisi broker dan margin sebelum market order dikirim., validate_market_order(), calculate_order_margin(), get_closed_deal_by_position(), get_current_prices(), get_open_positions(), get_position_ticket_from_deal(), get_recent_new_position_ticket() (+10 more)

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

### Community 28 - "main"
Cohesion: 0.26
Nodes (12): main(), notify_bot_started(), notify_bot_stopped(), notify_daily_drawdown_hit(), notify_error(), notify_trade_closed(), notify_trade_opened(), notifier.py Mengirim notifikasi ke Telegram saat bot start, stop, error, atau ke (+4 more)

### Community 29 - "export_project_docx.py"
Cohesion: 0.32
Nodes (11): Document, add_code_block(), add_inline(), add_page_number(), add_table(), configure_document(), export(), Path (+3 more)

### Community 30 - "shadow_tracker.py"
Cohesion: 0.25
Nodes (8): DataFrame, Catat hasil virtual sinyal AI yang diterima dan ditolak tanpa mengirim order., Selesaikan simulasi SL/TP; bila keduanya kena satu candle, hitung loss., _read(), record(), resolve(), _write(), ShadowTrackerTests

### Community 32 - "position_manager.py"
Cohesion: 0.25
Nodes (5): modify_position_sltp(), Ubah SL/TP posisi tanpa mengubah volume., manage(), Break-even dan trailing stop yang hanya menggeser SL ke arah lebih aman., PositionManagerTests

## Knowledge Gaps
- **468 isolated node(s):** `graphify`, `Fitur`, `Menjalankan dari source code`, `Pemakaian pertama`, `Membuat file EXE` (+463 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run_cycle()` connect `run_cycle` to `ai_trader.py`, `position_manager.py`, `trade_logger.py`, `risk_manager.py`, `learner.py`, `runtime_guard.py`, `test_next_stage_guards.py`, `main`, `mt5_connector.py`, `market_filters.py`, `main`, `shadow_tracker.py`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Why does `Panduan Lengkap AI Trading Bot untuk Pemula` connect `Panduan Lengkap AI Trading Bot untuk Pemula` to `2. Istilah dasar yang harus dipahami`, `8. Pengaturan desktop: panduan lengkap`?**
  _High betweenness centrality (0.011) - this node is a cross-community bridge._
- **Why does `8. Pengaturan desktop: panduan lengkap` connect `8. Pengaturan desktop: panduan lengkap` to `Panduan Lengkap AI Trading Bot untuk Pemula`?**
  _High betweenness centrality (0.009) - this node is a cross-community bridge._
- **What connects `graphify`, `Fitur`, `Menjalankan dari source code` to the rest of the system?**
  _468 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `ai_trader.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08081632653061224 - nodes in this community are weakly interconnected._
- **Should `8. Pengaturan desktop: panduan lengkap` be split into smaller, more focused modules?**
  _Cohesion score 0.045454545454545456 - nodes in this community are weakly interconnected._
- **Should `8. Pengaturan desktop: panduan lengkap` be split into smaller, more focused modules?**
  _Cohesion score 0.045454545454545456 - nodes in this community are weakly interconnected._