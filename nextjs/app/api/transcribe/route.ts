import { NextResponse } from "next/server";

export async function POST(req: Request) {
    const formData = await req.formData();
    const file = formData.get("audio") as Blob;

    if (!file) return NextResponse.json({error: "No file uploaded"}, {status: 400});

    const buffer = await file.arrayBuffer();
    const response = await fetch(process.env.NEXT_PUBLIC_API_GATEWAY_URL!, {
        method: "POST",
        headers: { "Content-Type": "applications/octet-stream"},
        body: Buffer.from(buffer),
    });

    const data = await response.json();
    return NextResponse.json(data);
}