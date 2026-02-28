import { useTranslations } from "next-intl";

export default function HomePage() {
  const t = useTranslations("home");

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-primary-600 mb-4">
          Aquafin
        </h1>
        <p className="text-lg text-slate-600 max-w-md">
          {t("tagline")}
        </p>
        <div className="mt-8 flex gap-4 justify-center">
          <a
            href="/it/dashboard"
            className="rounded-lg bg-primary-600 px-6 py-3 text-white font-medium hover:bg-primary-700 transition-colors"
          >
            {t("getStarted")}
          </a>
        </div>
      </div>
    </main>
  );
}
