import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import { auth, db } from "../firebaseConfig";
import { onAuthStateChanged, signOut } from "firebase/auth";
import {
  collection,
  addDoc,
  getDocs,
  Timestamp,
  query,
  orderBy,
} from "firebase/firestore";

type Booking = {
  id: string;
  customerName: string;
  service: string;
  date: string;
  note?: string;
  createdAt: any;
};

export default function Dashboard() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);

  const [customerQuestion, setCustomerQuestion] = useState("");
  const [shopType, setShopType] = useState("مطعم");
  const [smartReply, setSmartReply] = useState("");
  const [smartLoading, setSmartLoading] = useState(false);

  const [contentType, setContentType] = useState("عرض يومي");
  const [socialContent, setSocialContent] = useState("");
  const [contentLoading, setContentLoading] = useState(false);

  const [customerName, setCustomerName] = useState("");
  const [service, setService] = useState("");
  const [date, setDate] = useState("");
  const [note, setNote] = useState("");
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [bookingLoading, setBookingLoading] = useState(false);

  const [report, setReport] = useState("");
  const [reportLoading, setReportLoading] = useState(false);

  useEffect(() => {
    const unsub = onAuthStateChanged(auth, (u) => {
      if (!u) {
        router.push("/");
      } else {
        setUser(u);
        fetchBookings();
      }
    });
    return () => unsub();
  }, []);

  const handleLogout = async () => {
    await signOut(auth);
    router.push("/");
  };

  const generateSmartReply = async () => {
    if (!customerQuestion) return;
    setSmartLoading(true);
    setSmartReply("");
    try {
      const res = await fetch("/api/generateSmartReply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ shopType, question: customerQuestion }),
      });
      const data = await res.json();
      setSmartReply(data.reply || "");
    } catch {
      setSmartReply("حدث خطأ أثناء توليد الرد.");
    } finally {
      setSmartLoading(false);
    }
  };

  const generateSocialContent = async () => {
    setContentLoading(true);
    setSocialContent("");
    try {
      const res = await fetch("/api/generateSocialContent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ shopType, contentType }),
      });
      const data = await res.json();
      setSocialContent(data.content || "");
    } catch {
      setSocialContent("حدث خطأ أثناء توليد المحتوى.");
    } finally {
      setContentLoading(false);
    }
  };

  const createBooking = async () => {
    if (!customerName || !service || !date) return;
    setBookingLoading(true);
    try {
      await addDoc(collection(db, "bookings"), {
        userId: user?.uid,
        customerName,
        service,
        date,
        note,
        createdAt: Timestamp.now(),
      });
      setCustomerName("");
      setService("");
      setDate("");
      setNote("");
      await fetchBookings();
    } finally {
      setBookingLoading(false);
    }
  };

  const fetchBookings = async () => {
    if (!auth.currentUser) return;
    const qRef = query(
      collection(db, "bookings"),
      orderBy("createdAt", "desc")
    );
    const snap = await getDocs(qRef);
    const data: Booking[] = [];
    snap.forEach((doc) => {
      const d = doc.data() as any;
      if (d.userId === auth.currentUser?.uid) {
        data.push({
          id: doc.id,
          customerName: d.customerName,
          service: d.service,
          date: d.date,
          note: d.note,
          createdAt: d.createdAt,
        });
      }
    });
    setBookings(data);
  };

  const generateReport = async () => {
    setReportLoading(true);
    setReport("");
    try {
      const res = await fetch("/api/getReport", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ bookings }),
      });
      const data = await res.json();
      setReport(data.report || "");
    } catch {
      setReport("حدث خطأ أثناء توليد التقرير.");
    } finally {
      setReportLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b bg-white">
        <div className="max-w-6xl mx-auto flex justify-between items-center p-4">
          <div className="font-bold text-lg">ShopPilot AI – Dashboard</div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-600">
              {user?.email || "حساب"}
            </span>
            <button
              onClick={handleLogout}
              className="px-3 py-1 text-sm border rounded"
            >
              خروج
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-4 space-y-6">
        {/* shop type */}
        <section className="bg-white rounded shadow p-4 flex flex-wrap gap-4 items-center justify-between">
          <div>
            <h2 className="font-semibold mb-1">معلومات النشاط</h2>
            <p className="text-sm text-gray-600">
              اختر نوع نشاطك ليتم تخصيص الردود والمحتوى.
            </p>
          </div>
          <select
            className="border rounded px-3 py-2 text-sm"
            value={shopType}
            onChange={(e) => setShopType(e.target.value)}
          >
            <option>مطعم</option>
            <option>مقهى</option>
            <option>صالون</option>
            <option>ورشة</option>
            <option>محل ملابس</option>
            <option>عيادة بسيطة</option>
            <option>أخرى</option>
          </select>
        </section>

        {/* Smart Replies */}
        <section className="bg-white rounded shadow p-4">
          <h2 className="font-semibold mb-2">الردود الذكية على العملاء</h2>
          <p className="text-sm text-gray-600 mb-3">
            اكتب سؤالاً من عميلك وسيقوم ShopPilot AI بتوليد رد مهني ومناسب.
          </p>
          <textarea
            className="w-full border rounded px-3 py-2 text-sm mb-3"
            rows={3}
            placeholder="مثال: هل يوجد لديكم حجز اليوم الساعة 8 مساء لشخصين؟"
            value={customerQuestion}
            onChange={(e) => setCustomerQuestion(e.target.value)}
          />
          <button
            onClick={generateSmartReply}
            disabled={smartLoading}
            className="px-4 py-2 text-sm rounded bg-black text-white disabled:opacity-60"
          >
            {smartLoading ? "جاري توليد الرد..." : "توليد رد ذكي"}
          </button>

          {smartReply && (
            <div className="mt-3 border rounded bg-gray-50 p-3 text-sm whitespace-pre-wrap">
              {smartReply}
            </div>
          )}
        </section>

        {/* Social Content */}
        <section className="bg-white rounded shadow p-4">
          <h2 className="font-semibold mb-2">محتوى السوشيال ميديا</h2>
          <div className="flex flex-wrap items-center gap-3 mb-3">
            <span className="text-sm text-gray-600">
              نوع المحتوى الذي تريد إنشاءه:
            </span>
            <select
              className="border rounded px-3 py-2 text-sm"
              value={contentType}
              onChange={(e) => setContentType(e.target.value)}
            >
              <option>عرض يومي</option>
              <option>منشور إنستغرام</option>
              <option>منشور فيسبوك</option>
              <option>رسالة واتساب ترويجية</option>
              <option>إعلان مدفوع بسيط</option>
            </select>
            <button
              onClick={generateSocialContent}
              disabled={contentLoading}
              className="px-4 py-2 text-sm rounded bg-black text-white disabled:opacity-60"
            >
              {contentLoading ? "جاري التوليد..." : "توليد محتوى جاهز"}
            </button>
          </div>
          {socialContent && (
            <div className="mt-3 border rounded bg-gray-50 p-3 text-sm whitespace-pre-wrap">
              {socialContent}
            </div>
          )}
        </section>

        {/* Bookings */}
        <section className="bg-white rounded shadow p-4">
          <h2 className="font-semibold mb-2">الحجوزات</h2>
          <div className="grid md:grid-cols-4 gap-3 mb-3">
            <input
              className="border rounded px-3 py-2 text-sm"
              placeholder="اسم العميل"
              value={customerName}
              onChange={(e) => setCustomerName(e.target.value)}
            />
            <input
              className="border rounded px-3 py-2 text-sm"
              placeholder="الخدمة / الطاولة / نوع الحجز"
              value={service}
              onChange={(e) => setService(e.target.value)}
            />
            <input
              className="border rounded px-3 py-2 text-sm"
              placeholder="التاريخ والوقت (مثال: 2025-11-22 20:00)"
              value={date}
              onChange={(e) => setDate(e.target.value)}
            />
            <input
              className="border rounded px-3 py-2 text-sm"
              placeholder="ملاحظة (اختياري)"
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </div>
          <button
            onClick={createBooking}
            disabled={bookingLoading}
            className="px-4 py-2 text-sm rounded bg-black text-white disabled:opacity-60"
          >
            {bookingLoading ? "جاري الإضافة..." : "إضافة حجز"}
          </button>

          <div className="mt-4">
            <h3 className="font-semibold mb-2 text-sm">آخر الحجوزات</h3>
            <div className="space-y-2 max-h-60 overflow-auto">
              {bookings.map((b) => (
                <div
                  key={b.id}
                  className="border rounded px-3 py-2 text-sm flex justify-between"
                >
                  <div>
                    <div className="font-medium">{b.customerName}</div>
                    <div className="text-xs text-gray-600">
                      {b.service} – {b.date}
                    </div>
                    {b.note && (
                      <div className="text-xs text-gray-500">{b.note}</div>
                    )}
                  </div>
                  <div className="text-xs text-gray-500">
                    {b.createdAt?.toDate?.().toLocaleString
                      ? b.createdAt.toDate().toLocaleString()
                      : ""}
                  </div>
                </div>
              ))}
              {bookings.length === 0 && (
                <div className="text-xs text-gray-500">
                  لا توجد حجوزات بعد.
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Reports */}
        <section className="bg-white rounded shadow p-4 mb-6">
          <h2 className="font-semibold mb-2">تقرير أسبوعي مبسط</h2>
          <p className="text-sm text-gray-600 mb-3">
            يقوم ShopPilot AI بتحليل الحجوزات الحالية ويقترح عليك توصيات لتحسين
            عملك.
          </p>
          <button
            onClick={generateReport}
            disabled={reportLoading}
            className="px-4 py-2 text-sm rounded bg-black text-white disabled:opacity-60"
          >
            {reportLoading ? "جاري إنشاء التقرير..." : "توليد تقرير الآن"}
          </button>
          {report && (
            <div className="mt-3 border rounded bg-gray-50 p-3 text-sm whitespace-pre-wrap">
              {report}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
