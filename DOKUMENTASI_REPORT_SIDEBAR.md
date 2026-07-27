# Panduan Report — Sidebar PT. Tunas Mitra Jaya

Panduan ini menjelaskan setiap report yang ada di section **Reports** pada sidebar: fungsinya, apa saja yang bisa dilihat, dan cara menggunakannya. Beberapa filter memang sengaja disembunyikan supaya tampilannya lebih simpel dan tidak membingungkan — detailnya ada di catatan tiap report.

## Daftar Isi

1. [Sales Report Detail](#1-sales-report-detail)
2. [Sales Report Summary](#2-sales-report-summary)
3. [Purchase Report Detail](#3-purchase-report-detail)
4. [Purchase Report Summary](#4-purchase-report-summary)
5. [Accounts Receivable](#5-accounts-receivable)
6. [AR Summary](#6-ar-summary)
7. [Accounts Payable](#7-accounts-payable)
8. [AP Summary](#8-ap-summary)
9. [Profit and Loss Statement](#9-profit-and-loss-statement)
10. [Balance Sheet](#10-balance-sheet)
11. [Gross Profit](#11-gross-profit)
12. [Cash Flow](#12-cash-flow)
13. [Stock Ledger](#13-stock-ledger)
14. [Stock Balance](#14-stock-balance)

---

## 1. Sales Report Detail

**Fungsi:** Melihat rincian **per item** dari setiap Sales Invoice — cocok untuk mengecek item apa saja yang terjual, ke customer mana, dan berapa nilainya per baris (bukan per invoice).

**Yang ditampilkan:** Invoice, Nama Customer, Nama Item, Deskripsi, Item Group, Tanggal, Qty, Satuan (UOM), Harga, Jumlah.

**Cara menggunakan:**
- Buka dari sidebar Reports → **Sales Report Detail**.
- Saat pertama dibuka, report sudah otomatis terisi data untuk bulan berjalan.
- Untuk melihat periode lain, ganti **From Date** / **To Date** di bagian atas lalu tekan Enter.
- Kalau setelah beberapa waktu rentang tanggalnya terasa "ketinggalan" (tidak otomatis update ke bulan berjalan), tinggal ganti manual ke tanggal yang diinginkan.

---

## 2. Sales Report Summary

**Fungsi:** Melihat ringkasan **per invoice** (bukan per item) — satu baris per Sales Invoice, untuk cek total penjualan per transaksi dan per customer dengan cepat.

**Yang ditampilkan:** Nomor Voucher, Tanggal, Nama Customer, Mata Uang, Net Total, Grand Total, Catatan (Remarks).

**Cara menggunakan:** Sama seperti Sales Report Detail — buka dari sidebar, sesuaikan From Date/To Date sesuai kebutuhan.

---

## 3. Purchase Report Detail

**Fungsi:** Versi pembelian dari Sales Report Detail — rincian **per item** dari setiap Purchase Invoice, termasuk supplier dan persentase kontribusi terhadap total.

**Yang ditampilkan:** Nama Item, Item Group, Deskripsi, Invoice, Tanggal, Nama Supplier, Qty, Satuan (UOM), Harga, Jumlah, % dari Grand Total.

**Cara menggunakan:** Sama seperti Sales Report Detail, tinggal konteksnya ke pembelian/supplier.

---

## 4. Purchase Report Summary

**Fungsi:** Ringkasan **per Purchase Invoice** — satu baris per invoice pembelian, untuk melihat total pembelian per supplier dengan cepat.

**Yang ditampilkan:** Nomor Voucher, Tanggal, Nama Supplier, Mata Uang, Net Total, Grand Total, Catatan (Remarks).

**Cara menggunakan:** Sama seperti Purchase Report Detail.

---

## 5. Accounts Receivable

**Fungsi:** Daftar piutang — invoice pelanggan yang belum lunas, beserta sudah berapa lama jatuh temponya (ageing).

**Yang ditampilkan:**
- Grafik ageing di bagian atas.
- Tabel per invoice: customer, akun piutang, jumlah tagihan, jumlah dibayar, sisa outstanding, dan pembagian umur (0-30, 31-60, 61-90, 91-120, 121+ hari).
- Bisa di-group berdasarkan customer, difilter berdasarkan customer, customer group, salesman, dsb.

**Catatan:** Filter Company sudah otomatis terisi, jadi tidak perlu diisi manual. Beberapa filter yang jarang dipakai (Finance Book, Cost Center, Project, Sales Partner, Territory, Show Linked Delivery Notes, Revaluation Journals) sengaja disembunyikan supaya tampilan lebih ringkas.

**Cara menggunakan:**
- Buka dari sidebar Reports → **Accounts Receivable**.
- Filter yang tersedia: Posting Date, Party Type, Party, Receivable Account, Customer Group, Payment Terms Template, Salesman, Ageing Based On, Calculate Ageing With, Ageing Range, dan beberapa checkbox (Group By Customer, Based On Payment Terms, Show Future Payments, Show Salesman, Show Remarks, In Party Currency, Group by Voucher).

---

## 6. AR Summary

**Fungsi:** Versi ringkas dari Accounts Receivable — satu baris per customer (bukan per invoice), menampilkan total piutang dan ageing per customer secara agregat.

**Yang ditampilkan:** Party Type, Party, Advance Amount, Invoiced Amount, Paid Amount, Credit Note, Outstanding, pembagian umur (<0, 0-30, 31-60, 61-90, 91-120, 121+), Total Amount, Territory, Customer Group, Mata Uang.

**Catatan:** Company sudah otomatis terisi. Filter Finance Book, Cost Center, Project, Sales Partner, dan Territory disembunyikan supaya tampilan lebih ringkas.

**Cara menggunakan:** Sama seperti Accounts Receivable, tapi hasilnya sudah teragregasi per customer — cocok untuk laporan ringkas tanpa perlu scroll banyak baris invoice.

---

## 7. Accounts Payable

**Fungsi:** Kebalikan dari Accounts Receivable — daftar hutang ke supplier (Purchase Invoice yang belum lunas) beserta ageing-nya.

**Yang ditampilkan:** Grafik ageing, tabel per Purchase Invoice: supplier, akun hutang, invoiced/paid/outstanding, ageing 0-30 s.d. 121+, nomor & tanggal tagihan supplier, dsb.

**Catatan:** Company sudah otomatis terisi. Filter Finance Book, Cost Center, Project, Revaluation Journals, dan Handle Employee Advances disembunyikan supaya tampilan lebih ringkas.

**Cara menggunakan:**
- Buka dari sidebar Reports → **Accounts Payable**.
- Filter yang tersedia: Posting Date, Party Type, Party, Payable Account, Payment Terms Template, Ageing Based On, Calculate Ageing With, Ageing Range, checkbox Group By Supplier, Based On Payment Terms, Show Remarks, Show Future Payments, In Party Currency, Group by Voucher.

---

## 8. AP Summary

**Fungsi:** Versi ringkas dari Accounts Payable — satu baris per supplier, total hutang dan ageing per supplier.

**Yang ditampilkan:** Party Type, Party, Advance Amount, Invoiced Amount, Paid Amount, Debit Note, Outstanding, ageing 0-30 s.d. 121+, Total Amount, Supplier Group, Mata Uang.

**Catatan:** Company sudah otomatis terisi. Filter Finance Book, Cost Center, Project, dan Revaluation Journals disembunyikan supaya tampilan lebih ringkas.

**Cara menggunakan:** Sama seperti Accounts Payable, hasilnya sudah teragregasi per supplier.

---

## 9. Profit and Loss Statement

**Fungsi:** Laporan laba rugi — pendapatan dikurangi beban dalam periode tertentu, untuk melihat apakah usaha untung atau rugi.

**Yang ditampilkan:** Grafik trend, tabel akun income/expense berjenjang (bisa di-collapse/expand per akun), opsi tampilkan persentase margin & growth.

**Cara menggunakan:**
- Buka dari sidebar Reports → **Profit and Loss Statement**.
- Pilih Company kalau belum otomatis terisi.
- Pilih Fiscal Year, atau ganti "Filter Based On" ke Date Range kalau mau rentang tanggal bebas.
- Pilih Periodicity (Monthly/Quarterly/Yearly) sesuai kebutuhan.
- Gunakan tombol "Set Level" di bagian bawah tabel untuk mengatur seberapa detail akun ditampilkan (level 1 = ringkas, makin tinggi makin detail).

---

## 10. Balance Sheet

**Fungsi:** Neraca — posisi aset, kewajiban (liability), dan modal (equity) perusahaan pada satu titik waktu tertentu.

**Yang ditampilkan:** Sama seperti Profit and Loss Statement (grafik, tabel berjenjang, filter periode), tapi untuk akun Asset/Liability/Equity.

**Cara menggunakan:** Sama seperti Profit and Loss Statement — pilih Company, pilih periode, atur level detail dengan "Set Level".

---

## 11. Gross Profit

**Fungsi:** Menghitung laba kotor per transaksi penjualan (selisih harga jual dengan harga pokok/modal), untuk melihat margin keuntungan per item, per invoice, atau kelompok lain.

**Yang ditampilkan:** Tabel per baris item terjual dengan kolom nilai beli/jual dan persentase gross profit, bisa dikelompokkan (**Group By**) — misalnya per Invoice, Item Code, Item Group, atau Customer.

**Catatan:** Company sudah otomatis terisi. Filter Sales Person, Warehouse, Cost Center, dan Project disembunyikan. Beberapa opsi Group By yang jarang dipakai (Warehouse, Territory, Sales Person, Project, Cost Center, Payment Term) juga sudah dihapus dari pilihan supaya lebih relevan.

**Cara menggunakan:**
- Buka dari sidebar Reports → **Gross Profit**.
- Isi From/To Date sesuai periode yang ingin dilihat.
- Pilih opsi **Group By** sesuai kebutuhan (mis. per Item untuk lihat margin per produk, per Customer untuk lihat margin per customer).

---

## 12. Cash Flow

**Fungsi:** Laporan arus kas — pergerakan kas masuk/keluar yang dikelompokkan jadi 3 kategori: Operasional, Investasi, dan Pendanaan, plus total perubahan kas bersih.

**Yang ditampilkan:** Grafik ringkas Net Cash from Operations/Investing/Financing/Net Change in Cash, tabel breakdown per kategori (bisa expand/collapse), opsi tampilkan Opening & Closing Balance.

**Catatan:** Company sudah otomatis terisi. Filter Finance Book, Cost Center, dan Project disembunyikan supaya tampilan lebih ringkas.

**Cara menggunakan:**
- Buka dari sidebar Reports → **Cash Flow**.
- Pilih Fiscal Year (atau ganti ke Date Range) dan Periodicity (Yearly/Monthly/Quarterly) sesuai kebutuhan.
- Klik tanda panah di kolom "Section" untuk expand/collapse detail tiap kategori arus kas.

---

## 13. Stock Ledger

**Fungsi:** Kartu stok — mencatat setiap pergerakan stok (masuk/keluar) per item secara kronologis, termasuk saldo berjalan dan nilai stok.

**Yang ditampilkan:** Tanggal, transaksi yang menyebabkan pergerakan stok (Sales Invoice, Purchase Invoice, Stock Mutation, dll), qty masuk/keluar, saldo berjalan, nilai stok.

**Catatan:** Company sudah otomatis terisi. Filter Warehouse, Batch No, Project, dan Enable Serial/Batch Bundle disembunyikan. Kolom Item, Warehouse, Project, dan Company juga tidak ditampilkan di tabel supaya lebih ringkas.

**Cara menggunakan:**
- Buka dari sidebar Reports → **Stock Ledger**.
- Isi From Date/To Date (wajib diisi).
- Pilih Item tertentu kalau mau fokus ke satu produk, atau kosongkan untuk lihat semua pergerakan stok.

---

## 14. Stock Balance

**Fungsi:** Saldo stok per item pada satu titik waktu — untuk mengecek berapa stok yang tersedia sekarang (atau di tanggal tertentu di masa lalu), termasuk nilai stok dan rata-rata harga beli.

**Yang ditampilkan:** Nama item, qty tersedia, nilai stok, rata-rata harga beli.

**Catatan:** Company sudah otomatis terisi. Filter Warehouse, Warehouse Type, Show Variant Attributes, Show Stock Ageing Data, Ignore Closing Balance, dan Show Dimension Wise Stock disembunyikan. Kolom Item, Warehouse, Reserved Stock, dan Company juga tidak ditampilkan di tabel supaya lebih ringkas.

**Cara menggunakan:**
- Buka dari sidebar Reports → **Stock Balance**.
- Isi To Date (cukup ini saja untuk lihat saldo per tanggal tertentu).
- Filter per Item Group atau Brand kalau mau fokus ke kategori produk tertentu.

---

*Kalau ada filter yang dibutuhkan tapi tidak muncul di salah satu report di atas, hubungi tim IT/developer untuk disesuaikan.*
