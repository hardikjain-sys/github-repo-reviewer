const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export async function reviewRepository(
    url: string,
    deep: boolean
) {
    const cleanedApiUrl = API_URL.replace(/\/+$/, "");

    const response = await fetch(`${cleanedApiUrl}/review`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            url,
            deep,
        }),
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Failed to review repository");
    }

    return data;
}