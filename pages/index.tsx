import { useState } from "react";
import { useRouter } from "next/router";
import { auth } from "../firebaseConfig";
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
} from "firebase/auth";

export default function HomePage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleAuth = async () => {
    setError("");
    setLoading(true);
    try {
      if (mode === "login") {
        await signInWithEmailAndPassword(auth, email, password);
      } else {
        await createUserWithEmailAndPassword(auth, email, password);
      }
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="w-full border-b bg-white">
        <div className="max-w-5xl mx-auto flex justify-between items-center p-4">
          <div className="font-bold text-xl">ShopPilot AI</div>
          <button
            onClick={() => {
              setMode("login");
            }}
            className="px-4 py-2 text-sm border rounded"
          >
            دخول
          </button>
        </div>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center px-4">
        <div className="max-w-3xl text-center mb-8">
          <h1 className="text-3xl md:text-4xl font-bold mb-4">
            مساعد ذكاء اصطناعي يدير تواصلك، حجوزاتك ومحتواك… تلقائياً
          </h1>
          <p className="text-gray-600">
            ShopPilot AI يساعد أصحاب المحلات الصغيرة (مطاعم، صالونات، مقاهي…)
            على الرد على العملاء، إنشاء محتوى يومي، وتنظيم الحجوزات بدون
            توظيف موظف إضافي.
          </p>
        </div>

        <div className="w-full max-w-md bg-white shadow rounded p-6">
          <h2 className="text-lg font-semibold mb-4 text-center">
            {mode === "login" ? "تسجيل الدخول" : "إنشاء حساب"}
          </h2>

          {error && (
            <div className="mb-4 text-sm text-red-600 bg-red-50 p-2 rounded">
              {error}
            </div>
          )}

          <div className="space-y-3">
            <input
              type="email"
              placeholder="البريد الإلكتروني"
              className="w-full border rounded px-3 py-2 text-sm"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />

            <input
              type="password"
              placeholder="كلمة المرور"
              className="w-full border rounded px-3 py-2 text-sm"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />

            <button
              onClick={handleAuth}
              disabled={loading}
              className="w-full py-2 rounded bg-black text-white text-sm font-semibold disabled:opacity-60"
            >
              {loading
                ? "جاري المعالجة..."
                : mode === "login"
                ? "دخول"
                : "إنشاء حساب"}
            </button>
          </div>

          <div className="mt-4 text-center text-sm">
            {mode === "login" ? (
              <>
                ليس لديك حساب؟{" "}
                <button
                  className="text-blue-600 underline"
                  onClick={() => setMode("register")}
                >
                  أنشئ حساباً جديداً
                </button>
              </>
            ) : (
              <>
                لديك حساب بالفعل؟{" "}
                <button
                  className="text-blue-600 underline"
                  onClick={() => setMode("login")}
                >
                  سجل الدخول
                </button>
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
