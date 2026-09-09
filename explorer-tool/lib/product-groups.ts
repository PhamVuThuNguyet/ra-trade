import type { DataTypeId, ProductGroupId } from "./catalog";

const GOODS_PRODUCT_GROUP_LABELS: Record<ProductGroupId, string> = {
  all_products: "All products",
  essential_commodities: "Essential commodities",
};

const SERVICES_PRODUCT_GROUP_LABELS: Record<ProductGroupId, string> = {
  all_products: "All Services",
  essential_commodities: "Essential Services",
};

export function labeledProductGroups(
  groups: { id: ProductGroupId; display_name: string }[],
  dataTypeId: DataTypeId,
): { id: ProductGroupId; display_name: string }[] {
  const labels = dataTypeId === "services" ? SERVICES_PRODUCT_GROUP_LABELS : GOODS_PRODUCT_GROUP_LABELS;
  return groups.map((group) => ({
    id: group.id,
    display_name: labels[group.id] ?? group.display_name,
  }));
}
