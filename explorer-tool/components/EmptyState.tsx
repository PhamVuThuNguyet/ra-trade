"use client";

type Props = {
  title: string;
  detail: string;
};

export function EmptyState({ title, detail }: Props) {
  return (
    <div className="empty" role="status">
      <h2>{title}</h2>
      <p>{detail}</p>
    </div>
  );
}
