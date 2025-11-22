import type { NextApiRequest, NextApiResponse } from "next";

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  const { shopType, contentType } = req.body as {
    shopType: string;
    contentType: string;
  };

  try {
    const prompt = `
أنت خبير تسويق لمحل من نوع: ${shopType}.
اكتب نصاً جاهزاً لـ "${contentType}" بالعربية، بأسلوب جذاب وبسيط، 
مع دعوة واضحة لاتخاذ إجراء.
لا تذكر أنك ذكاء اصطناعي.
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
        temperature: 0.8,
      }),
    });

    const data = await llmResponse.json();
    const content =
      data?.choices?.[0]?.message?.content ||
      "لم أتمكن من توليد محتوى في هذه اللحظة.";

    return res.status(200).json({ content });
  } catch (e) {
    console.error(e);
    return res.status(500).json({ error: "Internal error" });
  }
}
