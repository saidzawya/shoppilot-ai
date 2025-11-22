import type { NextApiRequest, NextApiResponse } from "next";

type Booking = {
  customerName: string;
  service: string;
  date: string;
  note?: string;
};

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  const { bookings } = req.body as { bookings: Booking[] };

  try {
    const bookingsText = bookings
      .slice(0, 50)
      .map(
        (b, idx) =>
          `${idx + 1}) العميل: ${b.customerName}, الخدمة: ${b.service}, التاريخ: ${b.date}, ملاحظة: ${
            b.note || "لا يوجد"
          }`
      )
      .join("\n");

    const prompt = `
أنت مستشار أعمال لنشاط تجاري صغير.
هذه بيانات تقريبية عن الحجوزات الحالية:

${bookingsText || "لا توجد حجوزات بعد."}

اكتب تقريراً مختصراً بالعربية يتكون من:
- فقرة تلخيص للحالة العامة
- 3 نقاط قوة
- 3 نقاط تحتاج تحسين
- 5 توصيات عملية لزيادة المبيعات وتحسين تجربة العملاء
`;

    const llmResponse = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
      },
      body: JSON.stringify({
        model: "gpt-4o-mini",
        messages: [{ role: "user", content: prompt }],
        temperature: 0.7,
      }),
    });

    const data = await llmResponse.json();
    const report =
      data?.choices?.[0]?.message?.content ||
      "لم أتمكن من توليد تقرير في هذه اللحظة.";

    return res.status(200).json({ report });
  } catch (e) {
    console.error(e);
    return res.status(500).json({ error: "Internal error" });
  }
}
