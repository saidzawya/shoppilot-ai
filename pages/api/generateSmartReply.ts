import type { NextApiRequest, NextApiResponse } from "next";

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  const { shopType, question } = req.body as {
    shopType: string;
    question: string;
  };

  if (!question) {
    return res.status(400).json({ error: "Missing question" });
  }

  try {
    const prompt = `
أنت مساعد خدمة عملاء لمحل من نوع: ${shopType}.
اكتب رداً لبقاً ومختصراً وعملياً على سؤال العميل التالي بالعربية:
"${question}"

احرص أن يكون الرد:
- مهني
- واضح
- يشجع على الحجز أو الطلب إن كان مناسباً.
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
    const reply =
      data?.choices?.[0]?.message?.content ||
      "لم أتمكن من توليد رد في هذه اللحظة.";

    return res.status(200).json({ reply });
  } catch (e) {
    console.error(e);
    return res.status(500).json({ error: "Internal error" });
  }
}
