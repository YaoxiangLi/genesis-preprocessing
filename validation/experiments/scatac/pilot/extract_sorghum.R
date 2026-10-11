connection <- gzcon(gzfile('/data/combined.RData.gz', 'rb'))
names <- load(connection)
close(connection)
print(names)
for (name in names) {
 x <- get(name)
 metadata <- attr(x, 'meta.data')
 if (!is.null(metadata)) {
  write.table(cbind(barcode=rownames(metadata),metadata),paste0('/out/',name,'-cells.tsv'),sep='\t',row.names=FALSE,quote=FALSE)
  print(dim(metadata)); print(colnames(metadata)); print(attr(x,'version'))
 }
 assays <- attr(x,'assays')
 if (!is.null(assays)) for (assay in names(assays)) {
  fragments <- attr(assays[[assay]],'fragments')
  if (!is.null(fragments)) for (i in seq_along(fragments)) {
   print(list(assay=assay, fragment=i, path=attr(fragments[[i]],'path'), hash=attr(fragments[[i]],'hash')))
  }
 }
}
