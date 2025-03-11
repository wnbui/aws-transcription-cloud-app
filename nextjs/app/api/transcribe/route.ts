import { NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_GATEWAY_URL!;

export async function POST(req: Request) {
    try {
        const formData = await req.formData();
        const file = formData.get("audio") as Blob;

        if (!file) { 
            return NextResponse.json({ error: "No file uploaded" }, { status: 400 }); 
        }

        const buffer = await file.arrayBuffer();

        // Send audio file to AWS API Gateway
        const response = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "applications/octet-stream" },
            body: Buffer.from(buffer),
        });

        if (!response.ok) {
            throw new Error("Failed to send audio to backend");
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        return NextResponse.json({ error: (error as Error).message }, { status: 400 });
    }
}

export async function GET(req: Request) {
    try {
        const url = new URL(req.url);
        const jobId = url.searchParams.get("job_id");

        if (!jobId) {
            return NextResponse.json({ error: "Missing job_id" }, { status: 400 });
        }

        // Fetch transcription result from AWS API Gateway
        const response = await fetch(`${API_URL}?action=fetch&job_id=${jobId}`);

        if (!response.ok) {
            throw new Error("Failed to fetch transcription status");
        }

    } catch (error) {
        return NextResponse.json({ error: (error as Error).message}, {status: 500 });
    }
}